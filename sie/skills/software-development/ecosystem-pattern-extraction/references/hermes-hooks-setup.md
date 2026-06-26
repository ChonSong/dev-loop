# Hermes Shell Hooks — Setup Guide

## Overview

Hermes has three hook systems. Shell hooks are the simplest — shell scripts declared in `config.yaml` that fire on lifecycle events (pre_tool_call, post_tool_call, pre_llm_call, on_session_end, etc.). No plugin authoring, no Python code.

## Our Hook Configuration

All scripts live in `~/.hermes/agent-hooks/`.

**`config.yaml` hooks block:**

```yaml
hooks:
  pre_tool_call:
    - matcher: "terminal|Bash"
      command: "~/.hermes/agent-hooks/block-dangerous-commands.sh"
      timeout: 5
  post_tool_call:
    - matcher: "write_file|patch|MultiEdit|Edit"
      command: "~/.hermes/agent-hooks/file-change-accumulator.sh"
      timeout: 5
    - matcher: "write_file|patch"
      command: "~/.hermes/agent-hooks/auto-format.sh"
      timeout: 10
  pre_llm_call:
    - command: "~/.hermes/agent-hooks/inject-git-context.sh"
      timeout: 5
  on_session_end:
    - command: "~/.hermes/agent-hooks/session-end-batch-checks.sh"
      timeout: 30
```

## Hook Scripts

### `hook-lib.sh` — Shared library

Source this in every hook script. Provides:

| Function | Purpose |
|----------|---------|
| `hook_is_enabled "id" "profiles"` | Returns 0 if hook should run, 1 if skipped by profile/disabled list |
| `hook_read_payload` | Reads stdin JSON into `$PAYLOAD`, `$TOOL_NAME`, `$TOOL_INPUT`, `$SESSION_ID`, `$CWD`, `$EXTRA` |
| `hook_get_input_field "key"` | Gets a field from `tool_input` JSON |
| `hook_accum_dir` | Returns session-scoped temp directory for accumulators |
| `hook_noop` | Emits `{}` (no-op response) |
| `hook_block "reason"` | Emits `{"action":"block","message":"..."}` (pre_tool_call only) |
| `hook_context "text"` | Emits `{"context":"..."}` (pre_llm_call only) |
| `hook_log "LEVEL" "msg"` | Appends to `~/.hermes/logs/agent-hooks.log` |

### `block-dangerous-commands.sh` — PreToolUse safety

Profile: `minimal,standard,strict` (always on)  
Blocks: `rm -rf /`, destructive `dd` to block devices, `chmod -R 000 /`, fork bombs

### `file-change-accumulator.sh` — PostToolUse accumulator

Profile: `standard,strict`  
Tracks edited `.py/.js/.ts/.tsx/.jsx/.css/.html` paths per-session in `/tmp/hermes-hooks/edited-files-$SESSION_ID`. Deduplicates with `sort -u`. Used by `session-end-batch-checks.sh` at session end.

### `auto-format.sh` — PostToolWrite auto-formatter

Profile: `standard,strict`  
Runs `ruff format` on `.py` files after every `write_file` or `patch`.

### `inject-git-context.sh` — PreLLmCall context

Profile: `standard,strict`  
Injects branch name and change counts (staged/unstaged/untracked) into every LLM turn via `{"context":"..."}`. No-ops silently if not in a git repo.

### `session-end-batch-checks.sh` — SessionEnd batch

Profile: `standard,strict`  
The **Stop-as-aggregation** pattern. Reads the accumulator file from the session, runs `ruff format --check` and `ruff check` on all accumulated Python files, then cleans up. Injects results as context into the next turn.

## Runtime Gating

Set these env vars to control hooks without editing config:

```bash
export HERMES_HOOK_PROFILE=minimal    # Only safety hooks run
export HERMES_HOOK_PROFILE=standard   # Default — safety + quality + context
export HERMES_HOOK_PROFILE=strict     # All hooks including extra guardrails

export HERMES_DISABLED_HOOKS=pre:llm:git-context,post:write:accumulate
```

Pass per-session:
```bash
HERMES_HOOK_PROFILE=minimal hermes chat
```

## Consent Model

Each `(event, command)` pair prompts for approval on first run. Decisions persist to `~/.hermes/shell-hooks-allowlist.json`. Bypass with:
- `hermes --accept-hooks chat`
- `HERMES_ACCEPT_HOOKS=1`
- `hooks_auto_accept: true` in config.yaml

For cron jobs, use `HERMES_ACCEPT_HOOKS=1` or the hooks_auto_accept config since cron runs non-interactively.

## Diagnostics

```bash
hermes hooks list          # Show all configured hooks + consent status
hermes hooks test pre_tool_call --for-tool terminal   # Test-run against a synthetic payload
hermes hooks doctor        # Full health check — exec bits, consent, mtime, timing
hermes hooks revoke "path/to/hook.sh"   # Remove consent for a hook
```

## Adding a New Hook

1. Write the script in `~/.hermes/agent-hooks/`
2. Source `hook-lib.sh` and call `hook_is_enabled` + `hook_read_payload`
3. Add entry to `hooks:` section in `~/.hermes/config.yaml`
4. Run `hermes hooks doctor` to validate
5. `hermes hooks --accept-hooks chat` to consent on first run
