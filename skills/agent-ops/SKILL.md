---
name: agent-ops
description: "Use when starting complex tasks, debugging recurring failures, before commits, or when the agent is about to make many similar tool calls. Three systems: gotcha for scenario-specific gotcha memory, gated-terminal for hard abort on runaway terminal use, validate for JSON schema validation. Located at /workspace/agent-ops/."
---

# Agent Ops — three systems for fewer failures

Three independent tools that fix the three most expensive failure modes in the prior session history:

| System | Fixes | Evidence |
|---|---|---|
| `gotcha` | "Re-discover same bug across N sessions" | 5 sessions × 250 msgs re-debugging tunnel 404 |
| `gated-terminal` | "Repeat failing command 100+ times" | 136 terminal calls in one session violating 5-call SOUL rule |
| `validate` | "Crash on `.get()` of null API field" | 4x AttributeError NoneType.get in one session |

## Quick start

```bash
# 1. Surface relevant gotchas before starting work
GOTCHA=/workspace/agent-ops/gotchas/cli.py
python3 $GOTCHA show --file <file-you're-touching> --command <cmd-you're-running>

# 2. Wrap terminal calls to hard-abort on runaway retries
GATED=/workspace/agent-ops/enforcement/gated-terminal.py
# Use instead of bare terminal:
python3 $GATED <command> [args...]
# Override (sparingly): GATED_BUDGET_OVERRIDE=1 python3 $GATED <command>
# Check budget: python3 $GATED --status

# 3. Validate API JSON before parsing
VAL=/workspace/agent-ops/evidence/validate.py
python3 $VAL cloudflare-api-generic.json < api-response.json
python3 $VAL cloudflare-api-generic.json --curl "curl -s -H 'Auth: Bearer xxx' https://api..."
```

## When to use each

### `gotcha show` — call this FIRST when:
- Touching a file/directory you've debugged before (cloudflare-tunnel, linkedin, .hermes/cron)
- Seeing an error pattern from `MEMORY.md` (1033, cfd_tunnel, control stream, etc.)
- Starting a task similar to one in the session log

Don't call when: task is novel, single-tool-call, or already covered by an in-context skill.

### `gated-terminal` — wrap your calls when:
- Debugging (high retry risk)
- Running long batch operations
- Inside a subagent that might loop

Don't wrap when: single exploratory command, interactive tool, the command legitimately needs to retry (e.g., polling).

### `validate` — call when:
- Parsing JSON from an external API you've called before
- The schema exists in `/workspace/agent-ops/evidence/schemas/`
- You're about to `.get()` on a response field

Don't call when: response is a known stable shape, schema doesn't exist yet (add one).

## Gotcha lifecycle

1. New failure → `python3 $GOTCHA/cli.py add <id> "summary" --fix "..."` (provisional, occurrences=1)
2. Same failure seen again → `python3 $GOTCHA/cli.py bump <id>` (occurrences=2 → PROMOTED to authoritative)
3. Quarterly: `python3 $GOTCHA/cli.py review` (find provisional gotchas needing promotion)
4. Obsolete: `python3 $GOTCHA/cli.py retire <id>`

## Skill bundle (this directory)

```
agent-ops/
├── SKILL.md                                # this file — quick start + when to use
├── references/
│   ├── gotcha-system.md                    # gotcha format, triggers, lifecycle
│   ├── enforcement-patterns.md             # 3 enforcement patterns + when NOT to enforce
│   ├── case-study-tunnel-debug.md          # 1,250-message debugging spiral, calibrated ROI
│   └── argparse-cli-wrapper-pitfall.md     # the argparse REMAINDER bug + env-var fix
└── scripts/
    ├── show-context-gotchas.sh             # auto-detect context, run `gotcha show`
    ├── validate-api.sh                     # wrapper for validate.py
    └── commit-gate.sh                      # wrapper for pre-commit-gate.py
```

**Read order for a new session:** SKILL.md → references/case-study-tunnel-debug.md (calibrates expectations) → reference docs as needed for the specific sub-task. For Hermes session DB / storage issues, see `references/hermes-session-db-diagnostics.md`.

## Files (the systems themselves)

```
/workspace/agent-ops/
├── gotchas/
│   ├── cli.py              # `gotcha` command
│   ├── triggers.yaml       # file/command/error → set mapping
│   ├── sets/*.yaml         # gotcha definitions (cf-tunnel, linkedin, hermes-cron)
│   └── stats.json          # ROI tracking
├── enforcement/
│   ├── gated-terminal.py   # tool-call counter wrapper
│   └── pre-commit-gate.py  # syntax + secrets + tests + diff check
└── evidence/
    ├── validate.py         # JSON schema validator
    └── schemas/*.json      # API response schemas
```

## How this was built

See `/workspace/docs/plans/agent-efficiency-overhaul.md` for the design doc.
This skill was authored after the prior tunnel-debug session showed 1,250+ messages wasted on already-solved gotchas.

## Extending

Add a new gotcha set:
1. Create `gotchas/sets/<topic>.yaml` with 5-line entries
2. Add trigger to `gotchas/triggers.yaml`
3. `python3 gotchas/cli.py show <topic>` to verify

Add a new API schema:
1. Create `evidence/schemas/<api-name>.json` (Draft-07)
2. Add test cases to `validate.py` TEST_CASES list
3. `python3 evidence/validate.py --self-test` to verify

## Pitfalls (learned from real adoption)

These are class-level traps hit while building and using this system. Each has a `references/` file with the full story.

### 1. Investigation before destructive ops — always
When the symptom is "prompts fail immediately" or "Hermes is slow," the reflex is to prune the DB. **Don't.** First quantify: how big is the DB, what's consuming space, what config settings control retention. The DB hit 1.9GB because `auto_prune: false` was set and a webui tab leak created 438 empty sessions in one day. Pruning without understanding why it accumulated means it'll fill up again. See `references/hermes-session-db-diagnostics.md` for the full diagnosis sequence.

### 2. cwd-only trigger matching misses files in subdirectories
If your trigger file-pattern is `*linkedin*.py` and you call `gotcha show --cwd /workspace`, the matcher only checked `context["files"]` — it didn't scan the directory. **Fix**: when a cwd is given, `os.listdir(cwd)[:200]` and add each entry to the file list. Cap at 200 to avoid blowup on huge dirs. See `references/cwd-scanning-triggers.md`.

### 3. argparse `--flag value` collides with `nargs=REMAINDER`
If you build a wrapper like `gated-terminal <command> [args...]` and try to add `--budget-override <cmd>`, argparse will consume the next arg as the override's value, not pass it to the wrapped command. Symptom: exit code 0 on a command that should have exited 1. **Fix**: use an env var (`GATED_BUDGET_OVERRIDE=1`) for any wrapper-level flag. Reserve CLI flags for output mode (`--status`, `--json`) that don't take a value. See `references/argparse-override-pattern.md`.

### 4. Pre-commit hook output goes to STDERR, not STDOUT
When your tool becomes `.git/hooks/pre-commit`, the user only sees stderr. Stdout from the hook is captured by git's internals. **Fix**: write all status (✓/✗, reasons) to stderr; reserve stdout for any machine-readable data. Test by writing a tool that prints both — only stderr lines appear to the committer. See `references/pre-commit-hook-stderr.md`.

### 5. JSON Schema union types need `anyOf`, not `oneOf`
APIs that return either `{success: true, result: <obj>}` OR `{success: false, errors: [<obj>]}` are a union. Draft-07 `oneOf` requires exactly one to match (fragile); `anyOf` requires at least one (correct). **Fix**: use `anyOf` with `properties.success.const: true/false` to discriminate. See `references/json-schema-constraints.md`.

## Quick wrappers (`scripts/`)

- `scripts/quick-validate.sh <schema> [curl-args...]` — pipe a curl response through validate
- `scripts/add-gotcha.sh <set-name>` — interactive gotcha adder
- `scripts/session-gotcha-load.sh [workspace]` — calls `session-startup` with smart defaults

Note: scripts need `chmod +x` after cloning. Run once:
```bash
chmod +x /workspace/agent-ops/gotchas/scripts/*.sh
```

## Session analytics

For parsing tool call metrics, efficiency analysis, and session statistics from session JSON files, see `references/session-analytics-pattern.md`. Contains the correct JSON extraction pattern (tool_calls key, not content blocks), a reusable Python snippet, and baseline metrics from 2,303 sessions.

## Related / overlapping

The `adversarial-audit` skill covers commitment tracking and compliance checking — the detection side. This skill (`agent-ops`) covers gotchas and enforcement — the prevention side. Use both together.

The dormant `self-improving-agent` skill (in `openclaw-imports/`) describes
the same territory as a framework without a runnable implementation.
The gotcha system here is the working runtime. If you find yourself
re-explaining gotchas, point to this skill instead.
