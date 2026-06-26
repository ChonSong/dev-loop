# Task Exhaustion Recovery — Session Notes

## Context (Jun 16, 2026)

The GTO Wizard Clone had 9 completed + coach-approved tasks against AGENTS.md. `current_task` was `"tbd"`. The player cron had nothing to pick up and stopped making progress.

Meanwhile, the **study page** at `/study` rendered a strategy matrix with all-zero action percentages (0.0% for raise/call/fold) because the backend API couldn't serve live strategy data. The user asked "is work continuing still cant use study if latest being served."

## Root Cause Chain

1. **Tasks exhausted** — AGENTS.md only had 2 tasks defined (`fix-dev-environment`, `fix-variant-equity-pages`). Both completed. No one added the next set.
2. **Port mismatch** — The Docker compose mapped API to port 8001 (`8001:8000`). The frontend's `next.config.ts` proxied to `localhost:8000`. The production `next-server` was built with the old proxy pointing to `8002`/`8003`.
3. **No database seed data** — The strategy-lookup endpoint needs GTO ranges in PostgreSQL. They were never seeded. The endpoint returned 500 with a Python type error (`'dict' object has no attribute 'game_type'`).
4. **Dev loop had no self-recovery** — The player-agent's rule "Don't touch AGENTS.md" prevented adding new tasks even when the project was clearly stalled on user-facing work.

## Fix Applied

1. Rebuilt the API Docker image with updated requirements.txt (added missing deps: phevaluator, numpy, numba etc.)
2. Started the API directly on the host via `uv run uvicorn main:app --host 0.0.0.0 --port 8000` (Docker image had import path issues)
3. Changed docker-compose port from `8001:8000` → `8000:8000`
4. Installed `fakeredis` for Redis fallback
5. Rebuilt the Next.js frontend and restarted the production server
6. Added 4 new tasks to AGENTS.md
7. Updated checkpoint.json and master checkpoint

## What Should Have Happened

On detecting `current_task: "tbd"` with 9 approved tasks and a non-functional study page, the player should have:
1. Diagnosed what was broken (API port mismatch, no seed data, Python bug)
2. Added 3-4 concrete tasks to AGENTS.md targeting the real user-facing gaps
3. Updated the checkpoint to point at the first new task
4. Pushed the changes for the next cron tick to pick up

## Verification Commands

```bash
# API health
curl -s http://localhost:8000/api/v1/health

# Proxy health (frontend → API)
curl -s http://localhost:3000/api/v1/health

# Study data
curl -s "http://localhost:3000/api/v1/courses"
curl -s "http://localhost:3000/api/v1/variants"

# Strategy lookup (will be 404 until seed data exists)
curl -s "http://localhost:3000/api/v1/strategy-lookup?board=preflop&stack_depth=100&position=UTG"

# Deployed site
curl -s -o /dev/null -w "%{http_code}" https://wiz.codeovertcp.com/
```
