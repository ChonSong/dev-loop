# Backlog Scoring Model

When the Coach detects 0 remaining tasks in AGENTS.md, it generates the next batch. This document defines the scoring formula used to prioritise which gaps become tasks.

## Formula

```
priority_score = blocking_weight × confidence
```

## Weight Factors

| Factor | Weight | When to Apply |
|--------|--------|--------------|
| **Blocking** | 3.0× | Gap prevents ALL user work — API returns 500, proxy broken, frontend doesn't load |
| **User-facing** | 2.0× | User hits this immediately — strategy lookup errors, study page broken, ICM crashes |
| **Infra gap** | 1.5× | Infrastructure is fragile but not currently broken — no persistence, no seed data |
| **Polish** | 1.0× | Nice-to-have but not urgent — responsive layout, loading states, empty states |

## Confidence

| Value | Meaning |
|-------|---------|
| 1.0 | Verified — curl endpoint, checked DB, saw the error |
| 0.7 | Strong evidence — code review suggests the gap exists |
| 0.5 | Moderate evidence — plausible from architecture knowledge |
| 0.2 | Weak — hunch, not verified |

## Threshold

- **priority_score ≥ 1.0**: Candidate for next batch
- **priority_score < 1.0**: Defer — not worth the Coach's time budget

## Selection

Take the top 3-5 candidates by score descending. Tiebreaker: more user-facing wins.

## Worked Example

From the GTO Wizard recovery (June 16, 2026):

| Gap | Evidence | Weight | Conf. | Score | Batch? |
|-----|----------|--------|-------|-------|--------|
| API port mismatch → ECONNREFUSED | `curl :3000/api/v1/health` = 000 | 3.0 | 1.0 | 3.0 | ✅ 1st |
| Strategy lookup 500 (Python bug) | `curl strategy-lookup` = 500 | 2.0 | 1.0 | 2.0 | ✅ 2nd |
| No seed data in PostgreSQL | `curl strategy-lookup` = 404 (after fix) | 2.0 | 0.9 | 1.8 | ✅ 3rd |
| No API persistence (no systemd) | `ps aux\|grep uvicorn` = 1 PID | 1.5 | 1.0 | 1.5 | ✅ 4th |
| Solver Docker build fails | `docker compose build` = exit 1 | 1.5 | 1.0 | 1.5 | ✅ 5th |
| Study page shows 0.0% actions | Browser: raise/call/fold = 0 combos | 2.0 | 0.5 | 1.0 | ✅ 6th |
| Mobile nav overflow | Browser: horizontal scroll | 1.0 | 0.8 | 0.8 | ❌ Deferred |

Top 5 become the next batch. Mobile nav (0.8) defers.

## Derivation

This model combines:
- **self-improvement-engine**: `priority_weight × area_multiplier × recurrence × recency`
- **product-lens ICE**: `Impact × Confidence ÷ Effort` — simplified to Impact × Confidence
- **player-agent Task Exhaustion Recovery**: 5-tier priority ladder

## Updating

If you discover a gap category that doesn't fit the existing weights, add a new row to the weight table. The Coach uses this table at generation time.
