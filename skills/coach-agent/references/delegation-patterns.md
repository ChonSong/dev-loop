# Delegation Patterns for Coach Subagents

**Reference for structuring delegated tasks.** The Coach parent ALWAYS delegates heavy work. This file documents how to structure each delegation.

## When to Delegate

| Blocking work | Delegate to | Toolsets | Why |
|---------------|-------------|----------|-----|
| Run 3 test suites | 3 parallel subagents | `["terminal"]` | Each suite runs independently |
| Browser QA (load page, click, snapshot) | 1 subagent | `["browser", "web"]` | 5+ sequential browser calls |
| Compare reference vs live screenshot | 1 subagent | `["browser", "web"]` | vision_analyze + browser_vision |
| API health checks (curl 5+ endpoints) | 1 subagent | `["terminal", "web"]` | Independent probes |
| Investigate deploy log / proxy status | 1 subagent | `["terminal", "file"]` | Read configs, curl endpoints |
| Backlog investigation (multi-probe) | 3 parallel subagents | various | Phase 2.5/2.6 gap detection |

## Structuring Delegated Tasks

```python
# Good — parallel test suites (each independent)
delegate_task(tasks=[
    dict(goal="Run pytest API tests in gto-wizard-clone/apps/api", toolsets=["terminal"]),
    dict(goal="Run vitest frontend tests in gto-wizard-clone/apps/web", toolsets=["terminal"]),
    dict(goal="Run E2E tests in gto-wizard-clone/apps/web", toolsets=["terminal"]),
])

# Good — browser QA with focused context
delegate_task(
    goal="Load wiz.codeovertcp.com/study, check console errors, verify hand matrix renders",
    toolsets=["browser", "web"],
)

# Good — subagent loads a specialized skill for canvas testing
delegate_task(
    goal="Load polytopia.codeovertcp.com, click through tribe selection and start game, verify game state",
    context="Load skill_view('polytopia-game-qa') for the full canvas testing protocol with Phaser state reads",
    toolsets=["browser", "web"],
)
```

## When NOT to Delegate

- Reading checkpoints or AGENTS.md — these are small, do them directly
- Writing verdicts or updating checkpoints — the Coach must own the decision
- Git operations (commit, push, revert) — VCS should be single-threaded
- Single-file changes in Player tasks — just implement directly

## Delegation Ordering (Critical)

**The order of subagent delegations follows the review protocol steps. Do not reorder them.**

| Review Step | Delegation | When | Toolsets |
|-------------|------------|------|----------|
| **Step 1** | Visual comparison (reference vs live) | FIRST — before reading checkpoints, diffs, or anything else | `["browser", "web"]` |
| **Step 5** | Browser QA (page load, click, console) | After criteria review + diff reading | `["browser", "web"]` |
| **Step 5** | Test suites (API + frontend + E2E) | Same time as browser QA, parallel | `["terminal"]` |
| **Step 6** | Interaction workflow meta-analysis | After visual comparison, before verdict | `["browser", "web", "file"]` |

**Why ordering matters:**
- Step 1 visual comparison compares the clone's live pages against reference screenshots (static). It catches visual drift. It runs EVERY cycle regardless of new commits.
- Step 5 browser QA tests interactive functionality (click paths, state transitions, console errors). It runs only when reviewing new Player commits.
- Do NOT conflate them — they use similar toolsets but serve different purposes. If you skip Step 1 because "Step 5 handles it," you'll miss regression checks on cycles with no new commits.

**Pitfall:** Both visual comparison and browser QA use `["browser", "web"]` toolsets. Do not assume one subagent can do both — they have different goals, different checklists, and run at different times in the protocol. Keep them separate.

After delegate_task returns, read each subagent's summary and incorporate evidence into your verdict. Subagents are self-reporting — verify handles (HTTP status codes, test counts) rather than trusting narrative claims.

## Toolset Economy

Delegate with the minimum toolset each subagent needs:
- Filesystem-only work → `["terminal", "file"]` (no web — prevents curiosity waste)
- Research probe → `["web"]` (no terminal — can't run commands)
- Full implementation → `["terminal", "file", "web"]` (for docs lookup during coding)
- Never give a subagent the full parent toolset — it wastes tokens and risks scope creep

## Conflict Prevention

When delegating implementation tasks:
- **One subagent owns `__init__.py` and `main.py`** exclusively — never let two subagents both modify wiring files
- **Non-overlapping file patterns**: subagent A owns `apps/api/`, subagent B owns `apps/web/` — safe
- After delegation, always check for conflict markers: `grep -rn "<<<<<<\\|=======\\|>>>>>>" src/ 2>/dev/null`
