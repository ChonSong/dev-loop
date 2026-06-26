# Stuck Task Escalation Patterns

Real examples of stuck tasks that cost cycles when not escalated.

## Pattern: Silent React State Interaction Bug

**Project:** gto-wizard-clone
**Task:** fix-postflop-advance-turn-flow
**Symptom:** Clicking "Turn ▶" after dealing a flop — handler fires (0 console errors) but `boardStreet` state doesn't transition from 'flop' to 'turn'. Board cards silently update but street label stays on FLOP, the "River ▶" button never appears.

**Root cause suspected:** The 1940-line `study/page.tsx` has multiple effects and callbacks that reference `boardCards`/`boardStreet`. One of them (likely the solver API callback triggered after action selection, or a URL-param sync effect) calls `setBoardCards`/`setBoardStreet` with stale values, overriding the advance. The code at lines 374-383 is logically correct — the bug is upstream in the component's state interaction graph.

**Why it was stuck for cycles:**
- 0 JS console errors → nothing to grep for
- State gets overridden, not rejected → no error boundary fires
- Effect interaction requires tracing the full ~500-line state machine to find which effect fires second and clobbers the advance
- Each debug attempt starts from scratch (no reproduction script)
- 1940-line file makes `git bisect` on the bug tedious

**Escalation signal:** 3+ ticks on the same current_task with no commit. The handler code reads correctly — the bug is in the interaction between this handler and some other effect, not in the handler itself.

## Pattern: Stale Backend Responses Blocking Frontend Progression

**Project:** Any with API coupling
**Symptom:** Frontend makes API call, gets a response, but subsequent operations expect a different response shape. The frontend and backend were developed in different ticks and don't agree on the contract.

**Signal:** Frontend dev claims "backend returns wrong data" and backend dev claims "frontend sends wrong request" — both are partially right because the contract wasn't finalized before parallel work.

**Escalation:** Document the actual API contract (request shape + response shape) as a spec_gap, defer both, and let Coach author a contract task. Do not try to fix both sides in one tick.

## Pattern: Build/Deploy Flakiness

**Project:** Any with Docker or complex deploy
**Symptom:** Tests pass locally, build works locally, but deploy fails intermittently. Next.js cache invalidation, Docker layer caching, stale node_modules.

**Escalation:** After 2 attempts with different fixes, write a spec_gap and move on. Document the exact error + what you tried. These are rarely fixed by a third iteration of the same approach.
