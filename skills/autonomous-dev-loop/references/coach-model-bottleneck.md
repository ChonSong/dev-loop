# Coach Model Bottleneck — v4 Flash Failure Evidence

## Summary

The Coach cron job (`5e1bba516d87`) runs on `deepseek-v4-flash` — the same model as the Player. This is a regression from the original design intent (Coach on stronger model). The evidence below documents the specific failure modes this creates, gathered from analyzing 10+ Coach cron sessions.

## Finding 1: Delegation Aversion

Despite having `delegation` explicitly enabled in the Coach cron toolsets and a "SUBAGENT-FIRST directive" in the skill prompt, v4 flash consistently skips delegation:

| Session | Tool Calls | Delegations | Browser QA? | Verdict |
|---------|-----------|-------------|-------------|---------|
| `cron_20260625_063519` | ~8 | 1 | ❌ (curl only) | ✅ APPROVE |
| `cron_20260625_060518` | ~12 | 0 | ❌ (curl only) | ✅ APPROVE |
| `cron_20260625_020511` | ~15 | 0 | ❌ (curl only) | ✅ APPROVE |
| `cron_20260625_013510` | ~20 | 0 | ❌ (curl + files) | ✅ APPROVE |
| `cron_20260624_230405` | ~20 | 1 | ❌ (curl only) | ✅ APPROVE |

**Impact**: Coach does all work in its own context window — reading checkpoints, running git commands, and curling the live site. It never farms out browser QA, test suites, or reference comparisons to subagents, which means its context fills with noisy intermediate data instead of staying lean for reasoning.

## Finding 2: HTTP 200 as a Proxy for Browser QA

Coach verdicts consistently substitute `curl -o /dev/null -w "%{http_code}"` for real browser interaction. No session in the sample:
- Loaded a JavaScript-heavy page in a real browser
- Checked console errors via `browser_console()`
- Performed UI interactions (clicks, form fills, state transitions)
- Compared against the reference site via Tandem browser

**Concrete damage**: The postflop-advance-to-turn bug was **stagnant for 3+ cycles across 4+ Coach reviews** (approximately 90+ minutes). Each time the Coach curled the live site, got HTTP 200, and approved — while the feature was completely broken. A real browser interaction (click CALL → check if Advance to Turn appears → click it → verify street transition) would have caught this on cycle 1.

**System response**: Multiple hard rules added to the skill — "HTTP 200 + 0 console errors is NOT browser QA", "Browser QA is MANDATORY every cycle", "Scripts can't replace browser verification." These are monuments to flash's failure to do what a stronger model would do naturally.

## Finding 3: Brief Verdicts Without Deep Evidence

The typical Coach verdict follows this pattern:
1. "No new commits this cycle" (or minimal diff description)
2. "HTTP 200, live site healthy" (from curl, not browser)
3. "0 console errors" (unverified — from curl)
4. "Known bugs unchanged" (no fresh investigation)
5. "APPROVED"

Tool call counts: **10-20 total across two projects**. A thorough review of a canvas game + full-stack web app should involve 50+ tool calls with parallel delegations. The Coach pattern-matches its output from checkpoint files and git logs, not from actual page state.

## Finding 4: Session-Level Reliability Failures

Coach cron sessions have a documented pattern of loading the skill prompt and then producing **zero tool calls and zero output**:
- Session `cron_20260622_163528`: loaded 50KB+ skill, made zero tool calls for 10+ minutes before being killed
- Session `b4f35d68ede1_20260625_120027`: 1 message only — loaded skill, produced nothing
- Multiple "Player stalled" reports where ticks produced empty output

These are not timeouts — the session starts, loads the skill, and the model spins without producing any actual tool calls.

## Finding 5: Skills as a Monument to Model Failures

Every rule in the coach-agent SKILL.md traces to a specific flash failure in production:

| SKILL.md Rule | Failure It Prevents | Evidence |
|---|---|---|
| "HTTP 200 is NOT browser QA" | Substituting curl for real browser | 4+ cycles with advance-to-turn broken |
| "SUBAGENT-FIRST directive" | Not delegating complex sub-tasks | 5 consecutive sessions with 0 delegations |
| "Finding nothing is suspicious" | Claiming "0 issues" without deep look | Repeated approving of broken features |
| "Known-bug regression check" | Forgetting to re-check known bugs | advance-to-turn stagnant 6+ cycles |
| "Verify handles yourself" | Trusting subagent self-reports | Subagent said "page works" but missed major bugs |
| "No single-project shortcut" | Only checking one project | Coach missed GTO bugs while only on Polytopia |

The skill itself is now a monument to failures of this specific model. A stronger model wouldn't need most of these rules — it would naturally think before acting, delegate where appropriate, investigate where uncertain, and escalate where stuck.

## Root Cause: Same Model for Coach and Player

The original dev-loop design (Phase 2, Jun 14-17) specified:
- **Player** on flash (fast, cheap, executes)
- **Coach** on a stronger model (deep reasoning, catches flaws)

This was silently abandoned when the stronger model kept erroring (rate limits, 429s, fallbacks). Both now run on `deepseek-v4-flash`. The system's own docs acknowledge:
> "Pitfall: A Coach that never runs is worse than a Coach that shares the Player's model."

This single regression is the root cause of most compensation loop cycles. A Coach that shares the Player's model:
- Cannot catch what the Player missed (same blind spots)
- Needs external rules to compensate for its own limitations
- Produces shallow output that requires yet more rules
- Creates a self-defeating cycle of rule inflation → context reduction → shallower output

## Resolution (Applied 2026-06-25)

### Structural Fix

1. **Coach model changed** from `deepseek-v4-flash` (opencode-go) to `big-pickle` (opencode-zen) — Coach now runs on a substantially stronger model than the Player
2. **Coach SKILL.md simplified** 300→71 lines, removing flash-specific compensation rules
3. **Structural safeguards added**: pre-commit hooks rejecting \"Add E2E test for X\" tasks, auto-escalation cron for stagnant bugs (`escalate-stagnant-bugs.py`), checkpoint freshness check in Player skill

### Evidence of Success (First Big-Pickle Cycles, 2026-06-25)

**15:24 cycle** (first big-pickle review):
- **Found a P1 bug** on first run that flash missed for days (tribe selection sorted-index mismatch — every tribe starts wrong game)
- **Applied methodology gate correctly** — classified self-referential test as 🔴 METHODOLOGY FAILURE
- **Produced screenshots** during browser QA (flash never did this)

**19:43 cycle** (task ownership model validated):
- **Generated 3 fresh AGENTS.md tasks** — first time Coach ever replenished the backlog (`fix-filters-sub-tab-stub`, `fix-blockers-sub-tab-missing`, `fix-spaced-repetition-practice-mode`)
- **Cleaned 12 resolved spec_gaps** from checkpoint (previously they accumulated indefinitely)
- **Set current_task** to first new task in checkpoint (broke the "tbd" stall)
- Structural enforcement (pre-commit hooks, auto-escalation, freshness check) operated as safety nets, not procedural bloat

This validates the entire thesis: the model was the bottleneck, not the skill instructions.

### What Changed

| Before (Flash) | After (Big-Pickle) |
|----------------|-------------------|
| 10-20 tool calls, 0 delegations | Full browser QA, subagent delegation expected |
| curl -o /dev/null replaces browser | browser_navigate + browser_vision + screenshots |
| 6-word verdicts (\"HTTP 200, approved\") | Detailed findings with root cause analysis |
| Never generates AGENTS.md tasks | Step 4 generates 2-5 tasks from browser evidence |
| Skill bloat compensates for model limits | 71-line skill, model does the thinking |

### Ongoing Risk

The Player (`b4f35d68ede1`) still runs on `openrouter/owl-alpha` — an older weaker model. If the Player cannot execute the Coach's generated tasks, the loop stalls at the implementation layer rather than the review layer. Monitor Player output for task execution quality. If the Player consistently fails Coach after generation, consider upgrading the Player model too.

---

*This document was originally written to diagnose the same-model regression. With the Coach model fix applied (2026-06-25), the Coach side of the bottleneck is resolved. The Player model remains a potential secondary bottleneck.*

## Methodology for Future Analysis

To reproduce this analysis for a different model or system:

1. **Sample coach sessions**: Collect 5-10 consecutive cron session outputs
2. **Count tool calls by type**: file, git, curl, browser, delegation
3. **Map verdict claims to actual evidence**: Did the Coach claim to visit the page? Is there a browser_vision or browser_console call? Did any delegation happen?
4. **Trace specific bugs through cycles**: How many cycles was the same bug "unchanged" before a fix attempt?
5. **Measure preamble vs work ratio**: Character count of skill prompt loaded vs character count of actual investigation output
6. **Check for session stalls**: Count sessions where skill loaded but no tool output was produced

## See Also

- `autonomous-dev-loop/compensation-loop-analysis.md` — The meta-pattern that explains WHY the same-model regression creates a self-defeating feedback loop
- `coach-agent/SKILL.md` — Current skill with methodology gate, pitfalls, and review flow
- `agent-ops/session-analytics-pattern.md` — Tool-call metrics and efficiency analysis
