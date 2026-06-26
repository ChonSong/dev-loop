# Backlog Scoring Model

Weighted scoring formula for ranking what tasks to generate next, adapted from the self-improvement-engine's skill candidate scoring and product-lens's ICE prioritization.

## Weight Factors

| Factor | Weight | When to Apply |
|--------|--------|--------------|
| **Blocking** | 3.0× | This gap prevents ALL user work — API returns 500, proxy broken, frontend doesn't load |
| **User-facing** | 2.0× | User hits this immediately on normal use — strategy lookup errors, study page broken, ICM crashes |
| **Infra gap** | 1.5× | Infrastructure is fragile or incomplete — no persistence, no seed data, no health checks |
| **Polish** | 1.0× | Nice-to-have but not urgent — responsive layout, loading states, empty states |

## Formula

```
priority_score = weight_factor × confidence
```

- **weight_factor**: from the table above — pick the HIGHEST that applies
- **confidence**: 0.0-1.0 — how sure are you this gap actually exists? (verified by curl = 1.0, suspected from code review = 0.5, pure guess = 0.2)

**Threshold for action**: priority_score ≥ 1.0. Below that, it's not worth the Coach's time budget.

## Priority Ordering

After scoring, sort by score descending. Take the top 3-5 for task generation.

If two gaps have equal scores, the one that's more user-facing wins (infra → user-facing → polish tiebreaker).

## Example

From the GTO Wizard recovery (June 16, 2026):

| Gap | Evidence | Weight | Confidence | Score |
|-----|----------|--------|-----------|-------|
| API port mismatch → proxy returns ECONNREFUSED | curl :3000/api/v1/health = 000 | Blocking (3.0) | 1.0 | 3.0 |
| Strategy lookup 500 with Python bug | curl strategy-lookup = 500 "dict has no attribute" | User-facing (2.0) | 1.0 | 2.0 |
| No seed data in PostgreSQL | curl strategy-lookup = 404 (after fix) | User-facing (2.0) | 0.9 | 1.8 |
| No API persistence across reboots | ps aux|grep uvicorn = one PID, no systemd | Infra (1.5) | 1.0 | 1.5 |
| Solver Docker build fails | docker compose build solver = exit 1 | Infra (1.5) | 1.0 | 1.5 |
| Study page action buttons show 0.0% | browser shows all raise/call/fold = 0 combos | User-facing (2.0) | 0.5 | 1.0 |
| Mobile nav overflow | browser shows horizontal scroll | Polish (1.0) | 0.8 | 0.8 |

The top 5 (score ≥ 1.0) become tasks. The mobile nav (0.8) is deferred.

## Derivation

This model combines:
- **self-improvement-engine**: `priority_weight × area_multiplier × recurrency × recency` — the weighted multiplication pattern
- **product-lens ICE**: `Impact × Confidence ÷ Effort` — simplified to just impact × confidence since effort is harder to estimate upfront
- **player-agent Task Exhaustion Recovery**: The original investigation steps (curl endpoints, check DB, browser test) and the 5-tier priority ladder (infra → user-facing → data → features → polish)
