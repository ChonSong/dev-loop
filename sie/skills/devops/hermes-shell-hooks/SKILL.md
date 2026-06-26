---
name: hermes-shell-hooks
description: "Configure, author, test, and debug Hermes shell hooks — the drop-in script system for pre_tool_call, post_tool_call, pre_llm_call, on_session_end, and other lifecycle events. Covers the JSON wire protocol, profile gating (HERMES_HOOK_PROFILE), the accumulator/Stop-as-aggregation pattern, allowlist management, and the hermes hooks CLI."
version: 1.0.0
tags:
  - hermes
  - hooks
  - shell-hooks
  - automation
  - lifecycle
related_skills:
  - hermes-agent
  - cron-job-patterns
---

# Hermes Shell Hooks

Hermes has three hook systems. Shell hooks are the simplest: write a script, declare it in `config.yaml`, done. No Python plugin required.

## Hook Systems at a Glance

| System | Declared in | Language | Runs in | Can block tools |
|--------|------------|----------|---------|-----------------|
| Shell hooks | `hooks:` block in `~/.hermes/config.yaml` | Any (Bash, Python, Go, ...) | CLI + Gateway | Yes (`pre_tool_call`) |
| Plugin hooks | `ctx.register_hook()` in a plugin | Python only | CLI + Gateway | Yes |
| Gateway hooks | `HOOK.yaml` + `handler.py` in `~/.hermes/hooks/` | Python only | Gateway only | No |

## Configuration Schema

```yaml
# ~/.hermes/config.yaml
hooks:
  <event_name>:
    - matcher: "<regex>"          # Optional; pre/post_tool_call only
      command: "<shell command>"  # Required; runs via shlex.split, shell=False
      timeout: <seconds>          # Optional; default 60, capped at 300
hooks_auto_accept: false          # Skip TTY consent prompt for non-interactive runs
```

Valid events: `pre_tool_call`, `post_tool_call`, `pre_llm_call`, `post_llm_call`, `pre_api_request`, `post_api_request`, `on_session_start`, `on_session_end`, `on_session_finalize`, `on_session_reset`, `subagent_stop`.

## JSON Wire Protocol

**stdin** (piped to every hook invocation):

```json
{
  "hook_event_name": "pre_tool_call",
  "tool_name":       "terminal",
  "tool_input":      {"command": "rm -rf /"},
  "session_id":      "sess_abc123",
  "cwd":             "/home/user/project",
  "extra":           {}
}
```

`tool_name` and `tool_input` are `null` for non-tool events (`pre_llm_call`, `on_session_end`, etc.).

**stdout** (optional — hook returns JSON on stdout):

```json
// Block a pre_tool_call (either shape accepted):
{"decision": "block", "reason":  "Forbidden: rm -rf"}
{"action":   "block", "message": "Forbidden: rm -rf"}

// Inject context for pre_llm_call:
{"context": "Today is Friday, 2026-04-17"}

// Silent no-op (any empty or non-matching JSON):
{}
```

Malformed JSON, non-zero exit codes, and timeouts log a warning but never abort the agent loop.

## Creating a Hook Script

### Using hook-lib.sh (recommended)

The shared library at `~/.hermes/agent-hooks/hook-lib.sh` handles payload parsing, profile gating, and response helpers.

```bash
#!/usr/bin/env bash
# ~/.hermes/agent-hooks/my-hook.sh
source ~/.hermes/agent-hooks/hook-lib.sh

# Gate by profile — this hook only runs in standard or strict mode
hook_is_enabled "my:hook:id" "standard,strict" || { hook_noop; exit 0; }

# Parse stdin payload
hook_read_payload

# Optional: matcher-style filtering in script
[ "$TOOL_NAME" != "terminal" ] && { hook_noop; exit 0; }

# Do work...
cmd="$(hook_get_input_field "command")"

# Block:
hook_block "blocked: dangerous command"
# or no-op:
hook_noop
# or inject context:
hook_context "<some text>"
# or log:
hook_log "INFO" "hook fired for $TOOL_NAME"
```

### Response helpers reference

| Helper | Effect |
|--------|--------|
| `hook_noop` | Silent no-op — `{}` |
| `hook_block "reason"` | Block tool call — `{"action":"block","message":"..."}` |
| `hook_context "text"` | Inject into LLM — `{"context":"..."}` |
| `hook_log LEVEL msg` | Appends to `~/.hermes/logs/agent-hooks.log` |
| `hook_is_enabled id profiles` | Returns 0 if enabled, 1 if disabled by profile or `HERMES_DISABLED_HOOKS` |
| `hook_read_payload` | Sets `$PAYLOAD`, `$TOOL_NAME`, `$TOOL_INPUT`, `$SESSION_ID`, `$CWD`, `$EXTRA` |

## Profile Gating Pattern (from ECC)

Two env vars control hooks at runtime without editing config:

```bash
# Minimal profile — only lifecycle + safety hooks:
HERMES_HOOK_PROFILE=minimal hermes chat

# Standard profile — balanced quality + safety (default):
HERMES_HOOK_PROFILE=standard hermes chat

# Strict profile — extra guardrails:
HERMES_HOOK_PROFILE=strict hermes chat

# Skip specific hooks by comma-separated IDs:
HERMES_DISABLED_HOOKS=pre:llm:git-context,post:write:accumulate hermes chat
```

Each hook declares which profiles it belongs to via the second arg to `hook_is_enabled`:
- `"minimal,standard,strict"` — always on (safety hooks)
- `"standard,strict"` — default quality/automation hooks
- `"strict"` — extra guardrails only

## The Accumulator / Stop-as-Aggregation Pattern (from ECC)

**Problem:** Running `ruff check` or `eslint` after every edit makes the tool loop 4x slower.

**Solution:** Two-hook architecture borrowed from ECC:

1. **Lightweight PostToolUse accumulator** — records edited file paths to a session-scoped temp file. Fast (~5ms).
2. **Heavy on_session_end batch check** — reads the accumulator, runs all checks at once, then cleans up.

This maps to ECC's "Stop" aggregation pattern (Hermes has no native Stop event, so `on_session_end` is the closest equivalent).

Implementation structure:

```
post_tool_call accumulator (lightweight, <5ms)
  ↓ writes to /tmp/hermes-hooks/edited-files-<session_id>
on_session_end batch (heavy, up to 30s)
  ↓ reads accumulator, runs ruff/eslint on all tracked files
  ↓ deletes accumulator file
```

Hook IDs for this pattern use a naming convention: `post:write:accumulate` and `session:end:batch-checks`, matching ECC's `event:scope:action` format.

## Consent / Allowlist Model

Each unique `(event, command)` pair prompts for TTY approval on first use. Decisions persist to `~/.hermes/shell-hooks-allowlist.json`.

**Bypass for non-TTY runs** (gateway, cron, CI — any one suffices):
- `hermes --accept-hooks chat`
- `HERMES_ACCEPT_HOOKS=1 hermes chat`
- `hooks_auto_accept: true` in config.yaml (permanent bypass)

**Script edits are silently trusted** — the allowlist keys on the command string, not a content hash. `hermes hooks doctor` flags mtime drift.

## Testing and Debugging

```bash
# List all configured hooks:
hermes hooks list

# Test a hook with a synthetic payload:
hermes hooks test pre_tool_call --for-tool terminal --payload-file /tmp/payload.json

# Full diagnostic:
hermes hooks doctor

# Revoke consent for a hook:
hermes hooks revoke "~/.hermes/agent-hooks/my-hook.sh"
```

Hooks logs are in `~/.hermes/logs/agent-hooks.log` (if using `hook_log`).

## Pitfalls

- **Matcher mismatch** — The `matcher` field is a regex against tool names (e.g., `terminal|Bash`, `write_file|patch`). It only applies to `pre_tool_call` and `post_tool_call`. For all other events, omit the matcher.
- **Non-interactive consent** — Gateway and cron sessions are non-TTY. If `hooks_auto_accept` is false and you didn't pre-allowlist, hooks silently stay unregistered. Use `hermes hooks test` to trigger the consent flow, or pre-write the allowlist JSON.
- **auto-format race** — Writing a file and immediately running `ruff format` on it can race with the agent's next turn. Keep timeout ≤ 10s for format hooks.
- **Accumulator cleanup** — Always clean up accumulator files in the batch-check hook. Orphaned accumulators accumulate in `/tmp/hermes-hooks/`.
- **Path expansion** — Commands use `os.path.expanduser()` so `~/.hermes/agent-hooks/...` resolves correctly. Use full or `~`-prefixed paths, not relative.
- **First-publish consent on `hermes hooks test`** — The test command does NOT write the allowlist. Only a real session run with `--accept-hooks` or TTY consent does. Pre-write the allowlist for non-TTY setups.
