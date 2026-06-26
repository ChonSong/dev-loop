# ECC (Everything Claude Code) — Extracted Patterns

Source: https://github.com/affaan-m/ECC  
Version analyzed: 2.0.0 (June 2026)  
By: Affaan Mustafa  
License: MIT  
Stars: 211.9K+

## What It Is

A harness-native operating system for agentic work — 261 skills, 67 agents, 92 commands, 14+ MCP configs, 1723+ tests. Works across Claude Code, Codex, Cursor, OpenCode, Gemini, Zed, Qwen, Trae, GitHub Copilot. 10+ months of daily production evolution.

## Architecture

| Layer | Count | Location |
|-------|-------|----------|
| Agents (subagents) | 67 | `agents/*.md` |
| Skills | 261 | `skills/<name>/SKILL.md` |
| Commands | 92 | `commands/*.md` (legacy shims) |
| Hooks | 28+ | `hooks/hooks.json` + `scripts/hooks/*.js` |
| Rules | 10+ languages | `rules/{common,typescript,python,golang,...}/` |
| MCP configs | 14+ | `mcp-configs/` |
| Tests | 1723 | `tests/` |

## Extracted Patterns

### 1. Hook System

| Event | When | Purpose |
|-------|------|---------|
| PreToolUse | Before tool | Block/validate/inject warnings |
| PostToolUse | After tool | Accumulate state, lightweight checks |
| Stop | After response | **Batch heavy checks** (format, typecheck, lint) |
| SessionStart | Session opens | Load context, detect package manager |
| SessionEnd | Session closes | Cleanup, finalize |

**Key innovation — Stop-as-aggregation:** Lightweight PostToolUse hooks *accumulate* file paths. The Stop event then runs costly checks (eslint, typecheck, console.log audit) across all accumulated files in one batch. This avoids slowing the agent loop after every edit.

**Runtime gating via env vars** (no file edits):
```
ECC_HOOK_PROFILE=minimal|standard|strict
ECC_DISABLED_HOOKS=pre:write:doc-file-warning,post:bash:dispatcher
```

**27 hooks in production** — see `hermes-hooks-setup.md` in this references dir for the Hermes implementation.

### 2. Selective Install Architecture (Manifest-Driven)

Three-layer model: **Profiles → Components → Modules → Files**

```
User Request → Profile/Component → Dependency Resolution → Scaffold Plan → Apply → State Record
```

**Manifests:**
- `install-profiles.json` — 7 named bundles (minimal=3 modules, core=6, full=23)
- `install-modules.json` — 30+ modules with deps, targeted paths, harness support
- `install-components.json` — 50+ user-facing aliases like `capability:security`

**Key features:**
- Natural language search (`npx ecc consult "security reviews" --target claude`)
- Dependency resolution with cycle detection
- Target-specific adapters per harness (claude, cursor, codex, gemini)
- Install-state tracking prevents duplicate installations
- README explicitly warns against stacking install methods

### 3. Subagent Schema

Every agent is a single `.md` file with YAML frontmatter:

```yaml
---
name: typescript-reviewer
description: TypeScript/JavaScript code review. Invoke after writing .ts/.tsx/.js files.
tools: [Read, Grep, Glob]          # Read-only
model: sonnet
---
```

**Tool scoping dichotomy:**
- **Reviewers**: `[Read, Grep, Glob]` — inspect only
- **Fixers / Build resolvers**: `[Read, Write, Edit, Bash, Grep, Glob]` — write access

**Model routing:** Only `planner` and `architect` get `opus`. All other 65 agents use `sonnet`.

**Orchestration:** Simple routing table in AGENTS.md mapping situations to agents with "invoke proactively" rules — no complex routing engine.

### 4. Operational Maturity Signals

- **WORKING-CONTEXT.md**: Living doc tracking active queues, open PRs, constraints, execution notes
- **PR policy**: No merge-by-title, no merge-by-summary, explicit diff audit required
- **1723 tests** that must stay green with 80%+ coverage
- **Selective PR ingestion policy**: External-source PRs go through direct-port auditing rather than wholesale merge
- **Monetization**: OSS core (MIT) + ECC Pro GitHub App ($19/seat/mo) + Sponsors

## What We Implemented from ECC

See `~/.hermes/agent-hooks/` and the `hooks:` section in `~/.hermes/config.yaml`:

| Pattern | Implementation |
|---------|---------------|
| Stop-as-aggregation | `file-change-accumulator.sh` (PostToolUse) + `session-end-batch-checks.sh` (on_session_end) |
| Hook profile gating | `HERMES_HOOK_PROFILE` + `HERMES_DISABLED_HOOKS` env vars via `hook-lib.sh` |
| Pre-tool safety | `block-dangerous-commands.sh` (rm -rf, dd, chmod, fork bomb patterns) |
| Auto-format | `auto-format.sh` (ruff format on .py after Write) |
| Git context injection | `inject-git-context.sh` (git status into every pre_llm_call) |
