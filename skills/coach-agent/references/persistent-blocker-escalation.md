# Persistent Blocker Escalation — Normalised Blocker Pitfall

## The Pattern

When a deployed site returns 502 (or any hard failure) for multiple consecutive review cycles, Coach begins treating it as "pre-existing" and stops treating it as a review-blocking finding. This is the **normalised blocker** pattern.

### How It Manifests

| Cycle | Action | Verdict |
|-------|--------|---------|
| 1 | "Site 502 — blocker noted, cannot test UI" | FIX (blocker noted) |
| 2 | "Site still 502 — pre-existing, not addressing now" | APPROVE |
| 3+ | "Live site: 502 (pre-existing)" — one line in report | APPROVE |

### Why It's Dangerous

- **The blocker never gets fixed** — Coach's verdict prose is invisible to the Player. Only AGENTS.md tasks drive Player action.
- **Browser QA stops entirely** — the very thing that makes Coach valuable (interactive testing) is the first thing dropped.
- **Regression goes undetected** — a commit that breaks something unrelated to the 502 will not be caught because Coach never loads the repaired site.
- **The player gets no signal** — if Coach keeps approving despite a broken deploy, the Player has no reason to fix it.

## Evidence (2026-06-24)

Across 5 consecutive review cycles (12:07, 12:57, 13:19, 13:35, 13:38), the Coach recorded the same 502 on gto-wizard-clone:

```
Live site: 502 — pre-existing blocker (fix-e2e-build-exclusion not addressed)
```

Browser QA dropped from 9 navigates + 5 clicks + 5 visions (12:07 cycle, which was reviewing POM infrastructure) to 2 navigates + 1 click + 2 visions (13:38 cycle, which was reviewing gitignore cleanup). The blocker was used as justification to skip interactive testing even though the commit type also justified it.

The 502 blocker was **never converted into an AGENTS.md task** — it remained as verdict prose in review reports, invisible to the Player.

## Escalation Protocol

### At Cycle 1

When a deployed site fails (502/500/timeout):

1. Record it as a **finding** — do not silently pass
2. Check if the failure is caused by the current commit (`git revert HEAD && redeploy` test — if it resolves, the commit broke it)
3. If the failure pre-exists the commit: add it to AGENTS.md as a new task with `priority: critical`
4. Issue FIX — the missing blocker task is a quality gap

### At Cycle 2 (blocker persists, task exists)

1. Check AGENTS.md: does the blocker have an unaddressed task?
2. If yes: note "Task exists, not yet addressed" — still do NOT skip browser QA
3. **Fall back to cross-project regression QA** (see below)
4. APPROVE the commit only if the commit doesn't make the blocker worse

### At Cycle 3+ (blocker persists unaddressed)

1. The blocker is now a **systemic quality failure** — escalations exist
2. **Convert to REVERT** if: the current commit touches any code path that relates to the blocker, OR if no task was ever created for it
3. **Fall back to cross-project regression QA** — mandatory, not optional
4. Record a learning via SIE feedback: "persistent-blocker-not-escalated" pattern

### Cross-Project Fallback (Mandatory When Primary Site Is Down)

When the active project's deployed URL returns non-200:

1. Check master-checkpoint.json for **all active projects**
2. Pick the next-highest-priority project with a functioning deployed URL
3. Run full browser QA on that project instead
4. If no other project has a functioning URL: run the project's test suite from localhost (API + frontend + E2E) to verify nothing regressed
5. Report: "⚠️ Primary site [project] down (502). Fallback: QA'd [other project] — [N] navigations, [M] interactions, [K] findings."

This ensures Coach always exercises a browser in every cycle, even when the primary target is broken.
