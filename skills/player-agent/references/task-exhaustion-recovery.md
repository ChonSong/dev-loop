# Task Exhaustion Recovery (Safety Valve)

Triggered only when the Coach has failed to generate backlog tasks. Full recovery protocol.

## When to Trigger

At least one of these must be true:
1. `current_task` in `.checkpoint.json` is `"tbd"` (or the task ID from AGENTS.md doesn't exist)
2. Backlog tasks remaining < 3 (the Coach hasn't generated enough new work)
3. Coach hasn't reviewed any commits in >6h (Coach may be errored or stalled)
4. ALL entries in `completed[]` have `coach: "approved"` AND the project still has **obvious user-facing gaps**

**Do NOT gate on completed[] all being coach-approved.** If the loop is stalled because Coach errored, rate-limited, or fell behind, recover immediately without waiting for Coach approval. — the live site returns 500s, core pages error, study doesn't work, the app is running but no real user flow completes
4. **If a `FEATURES.yaml` exists** in the project root: there are `status: missing` entries not yet addressed. Read `FEATURES.yaml` and count `missing` items — if > 0, the project has known spec gaps.

## How to Diagnose What Tasks Are Needed

1. **Check the API**: `curl -s http://localhost:8000/api/v1/health` — does the backend even run?
2. **Check the proxy**: `curl -s http://localhost:3000/api/v1/health` — does the frontend→backend connection work?
3. **Check the live site**: `curl -s -o /dev/null -w "%{http_code}" https://wiz.codeovertcp.com/` — is the deployed app accessible?
4. **Check the deploy log**: `grep -c "Rollback\|error\|build failed" /home/sc/.hermes/logs/gto-wizard-deploy.log | tail -5` — did the last deploy fail?
5. **Check the browser**: Use `browser_navigate` to load key pages — do they render without console errors?
6. **Check the database**: Does PG have seed data? `docker exec gto-wizard-clone-postgres-1 psql -U postgres -d gto_wizard -c "SELECT count(*) FROM strategies"`

## Prioritization Rules

1. **Infrastructure that blocks ALL user work** — API not running, Docker services down, port mismatches, missing deps. Without these, nothing else works.
2. **Core user flow blockers** — strategy lookup returns 500, study page errors, solver not connected. Things the end user trips on immediately.
3. **Data seeding** — API is up but has no data to serve. Seed pre-computed strategies, course content, quiz questions.
4. **Feature gaps** — Pages that exist but are broken or non-functional (ICM calculator errors, variant pages that don't load, missing state handling).
5. **Polish** — Responsive layout, loading states, error states, empty states. Only when 1-4 are stable.

## How to Add Tasks

1. Read the current AGENTS.md
2. Add new tasks after the last completed task (don't delete or modify existing completed tasks — they're audit trail)
3. Each task must have: Description, Success criteria (measurable), Coach checks (verifiable)
4. Update `.checkpoint.json`: set `current_task` to the first new task's ID
5. Update master checkpoint: set `current_task` to the same
6. Commit: `chore: add user-facing tasks to AGENTS.md — [brief summary]`
7. Push: `git push origin main` — so the deploy timer picks it up

## Example Recovery (Jun 16)

After 9 completed + approved tasks, the dev loop was idle at `current_task: tbd`, but the study page couldn't fetch strategy data because:
- Docker API port (8001) didn't match frontend proxy (8000)
- No strategy data seeded in PostgreSQL
- Strategy-lookup endpoint had a Python type bug

Tasks added:
1. `keep-api-server-running` — systemd service for the API
2. `fix-strategy-lookup` — fix the `'dict' object has no attribute 'game_type'` bug
3. `seed-preflop-strategies` — populate PG with GTO ranges
4. `fix-solver-docker-build` — fix numpy/numba dependency conflict

## What NOT to Do in Recovery

- Don't add tasks that are repeats of already-completed work
- Don't add tasks without checking what's actually broken first
- Don't add more than 5 tasks in one batch — the loop needs to stay focused
- Don't remove or reorder existing AGENTS.md tasks — the coach validated them
- Don't skip the investigation step — it wastes cycles
- Don't add tasks about infrastructure that's already working — verify first
