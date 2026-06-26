# Cron Redesign Patterns — June 2026

Concrete cron job redesigns from analysis of a 47-day, 1.9GB state.db with 3,600+ sessions.

## Context

The system had:
- 1.9GB state.db (157K messages, 3,602 sessions)
- 701 empty webui sessions (0 messages — from a page-reload storm)
- 342 watchdog cron sessions (every 5 min, 10 messages each)
- 30+ auto-continue sessions per day
- 97% disk usage causing session failures ("prompts not responded to")

## Pattern 1: GTO Watchdog — Strip Overhead, Keep LLM Reasoning

**Before:**
```yaml
schedule: "*/5 * * * *"
# Full system prompt, full skills scan, full toolset
prompt: "Check GTO Wizard service health. curl and report HTTP status"
```
- 342 sessions, 3,240 messages of "service is up"
- ~4K tokens of system prompt (skills list alone = 270K chars)
- Full LLM used as a port-pinger

**After:**
```yaml
schedule: "*/15 * * * *"
enabled_toolsets: ["terminal"]    # only needs curl
# NO skills list — self-contained prompt
prompt: |
  Check GTO Wizard health at wiz.codeovertcp.com
  1. curl homepage — HTTP status + response time
  2. curl a key API endpoint
  3. Compare response time to last check (trend detection)
  4. If anything changed (status, latency spike >500ms), report details
  5. If all normal: [SILENT]
```
- Zero sessions if using no_agent, or 1 session/tick with enriched prompt
- LLM now used for trend detection, not port-pinging
- No skills list tax

## Pattern 2: Auto-Continue — Delegation Over Monolith

**Before:**
```yaml
schedule: "*/30 * * * *"
# Full everything — tries to do test+lint+build+QA in one session
prompt: "auto-continue-work: fix tests, lint, build, check deps..."
```
- Every run was 70-137 messages of one agent doing everything sequentially

**After:**
```yaml
schedule: "0 * * * *"
enabled_toolsets: ["delegation"]
skills: ["git-workflow"]
prompt: |
  Check auto-continue-log.md and git status for pending work.
  If there's a clear next step, delegate:

  delegate_task(
    goal="Run tests on <repo>, fix one failure if obvious",
    toolsets=["terminal", "file"],
    context="<exact paths and commands>"
  )

  delegate_task(
    goal="Lint sweep — run linter, fix warnings, format",
    toolsets=["terminal", "file"]
  )

  delegate_task(
    goal="Visual QA — build, screenshot, vision_analyze for regressions",
    toolsets=["terminal", "vision"]
  )

  If no clear work: [SILENT]
```
- Each subagent gets a focused goal → better skill-selector matching
- Subagents run in parallel (up to 3)
- Each subagent has a much smaller system prompt

## Pattern 3: HWC Canary Watch — Vision-Driven QA

**Before:**
```yaml
# Full browser_navigate from container (which often fails)
prompt: "Navigate to HWC, screenshot, check for errors"
```

**After:**
```yaml
enabled_toolsets: ["terminal", "vision"]
skills: ["ui-qa-pipeline", "deployment-audit"]
prompt: |
  1. curl the host endpoint to verify it's up
  2. If up, delegate visual QA
```

## Efficiency Analysis

| Job | Before (per tick) | After (per tick) | Savings |
|-----|-------------------|-------------------|---------|
| Watchdog | ~4K system + 270K skills + 10 LLM calls | ~2K system + ~5 LLM calls | ~97% token reduction |
| Auto-continue | ~4K system + 270K skills + 60-130 LLM calls | ~2K system + 3 subagents × ~20 calls | ~95% prompt overhead reduction |
| Canary | ~4K system + 270K skills + browser | ~2K system + vision call | ~95% prompt reduction |

## Key Lessons

1. **Skills list is the single biggest tax** — 270K chars in every cron job's system prompt. Use `skills: [...]` to skip it entirely.
2. **Enabled_toolsets strips unused tools** — Watchdog only needs `["terminal"]`, not browser/vision/delegation.
3. **Delegation beats monolith** — One focused subagent per task has a smaller prompt and better skill matching.
4. **Vision_analyze beats browser_navigate** — For visual QA, capture a screenshot + call vision model. More reliable than headless browser from container.
5. **Env vars override config** — `AUXILIARY_VISION_*` env vars in `.env` take precedence over `config.yaml`. Check both.
