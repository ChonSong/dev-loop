# ECC Hook System — Patterns Extracted

Source: [github.com/affaan-m/ECC](https://github.com/affaan-m/ECC) v2.0.0, ~211K stars.

## Overview

ECC ships 26+ hooks across 7 event types, 270+ skills, 67 agents. Its hook system informed our Hermes shell hooks implementation.

## Event Types (ECC vs Hermes Mapping)

| ECC Event | Hermes Equivalent | Purpose |
|-----------|------------------|---------|
| PreToolUse | pre_tool_call | Block dangerous commands, gate edits |
| PostToolUse | post_tool_call | Lightweight accumulators, auto-format |
| Stop | (*no exact match* — use on_session_end) | **Aggregation point**: run heavy checks once |
| SessionStart | on_session_start | Load context, detect package manager |
| SessionEnd | on_session_end | Persist state, cleanup |
| PreCompact | (*no Hermes equivalent*) | Save state before context compaction |

## The Stop-as-Aggregation Design

ECC's most important architectural insight: **don't run expensive checks after every edit**. Instead:

1. **PostToolUse accumulator** (fast, <5ms): Records which files changed. Does NOT run linters.
2. **Stop event** (heavy, up to 300s timeout): Reads accumulator, runs ALL checks (format, typecheck, console.log audit) across accumulated files, then clears the list.

This is why ECC can run `eslint`, `prettier`, and `tsc` in CI without slowing the interactive loop. The Stop event fires once per assistant response, not once per tool call.

In Hermes, we approximate this with `on_session_end` since there's no per-response Stop event. For per-turn aggregation, `pre_llm_call` can serve as a lightweight aggregation point.

## Hook Runtime Controls

ECC uses env vars instead of config-file edits:
- `ECC_HOOK_PROFILE=minimal|standard|strict`
- `ECC_DISABLED_HOOKS=pre:write:doc-file-warning,post:quality-gate`
- `ECC_DRY_RUN=1` — preview which hooks would fire without executing

The profile system: each hook declares its coverage as a CSV string. `isHookEnabled()` checks profile first, then disabled list.

## Hook ID Convention

ECC uses `event:scope:action` format:
- `pre:write:doc-file-warning` — PreToolUse, Write matcher, doc-file-warning script
- `post:bash:dispatcher` — PostToolUse, Bash matcher
- `stop:format-typecheck` — Stop event, format+typecheck
- `session:start:context-loader` — SessionStart

This naming makes it obvious what a hook does and which event it fires on.

## Key Implementation Details from ECC

- **Inlined Node.js bootstrap**: Each hook command starts with a self-contained plugin-root resolver that locates the ECC install dir. Makes hooks location-independent.
- **run-with-flags.js**: Central gate that checks profile/disabled/dry-run before dispatching. Avoids ~50ms spawn delay by trying `require()` first.
- **Exit code contract**: `0` = continue (may have warned), `2` = block (PreToolUse only). Other non-zero = logged but doesn't block.
- **First block wins**: When multiple hooks match, the first `{"action":"block"}` response is used. Python plugin hooks (registered first) take precedence over shell hooks (registered second).

## Full ECC Hook Inventory

| Event | ID | Matcher | Profile | Description |
|-------|----|---------|---------|-------------|
| PreToolUse | pre:bash:dispatcher | Bash | all | Bash preflight (quality, tmux, push, GateGuard) |
| PreToolUse | pre:write:doc-file-warning | Write | std,strict | Warn on ad-hoc doc filenames |
| PreToolUse | pre:edit-write:suggest-compact | Edit|Write | std,strict | Suggest compact at ~50 tool calls |
| PreToolUse | pre:observe:continuous-learning | * | std,strict | Capture tool use observations |
| PreToolUse | pre:governance-capture | Bash|Write|Edit|MultiEdit | std,strict | Capture governance events |
| PreToolUse | pre:config-protection | Write|Edit|MultiEdit | std,strict | Block changes to linter configs |
| PreToolUse | pre:mcp-health-check | * | std,strict | Check MCP server health |
| PreToolUse | pre:edit-write:gateguard-fact-force | Edit|Write|MultiEdit | strict | Block first edit per file |
| PreCompact | pre:compact | * | std,strict | Save state before compaction |
| SessionStart | session:start | * | all | Load context, detect pkg manager |
| PostToolUse | post:bash:dispatcher | Bash | std,strict | Bash postflight |
| PostToolUse | post:quality-gate | Edit|Write|MultiEdit | std,strict | Run quality gate after edits |
| PostToolUse | post:edit:design-quality-check | Edit|Write|MultiEdit | std,strict | Warn on template-looking UI |
| PostToolUse | post:edit:accumulator | Edit|Write|MultiEdit | std,strict | **Record edited file paths** |
| PostToolUse | post:edit:console-warn | Edit | std,strict | Warn about console.log |
| PostToolUse | post:governance-capture | Bash|Write|Edit|MultiEdit | std,strict | Capture from tool output |
| PostToolUse | post:session-activity-tracker | * | std,strict | Track tool calls |
| PostToolUse | post:observe:continuous-learning | * | std,strict | Capture results for learning |
| PostToolUse | post:ecc-metrics-bridge | * | std,strict | Session metrics |
| PostToolUse | post:ecc-context-monitor | * | std,strict | Alert on context exhaustion |
| PostToolUseFailure | post:mcp-health-check | * | std,strict | Track failed MCP calls |
| Stop | stop:format-typecheck | * | std,strict | **Batch format + typecheck** |
| Stop | stop:check-console-log | * | std,strict | Check for console.log in modified files |
| Stop | stop:session-end | * | std,strict | Persist session state |
| Stop | stop:evaluate-session | * | std,strict | Extract patterns for learning |
| Stop | stop:cost-tracker | * | std,strict | Token and cost metrics |
| Stop | stop:desktop-notify | * | std,strict | macOS notification |
| SessionEnd | session:end:marker | * | std,strict | Lifecycle marker |
