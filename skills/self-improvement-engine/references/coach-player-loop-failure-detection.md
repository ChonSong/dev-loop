# Coach/Player Loop Failure Detection Pattern

A capability bottleneck pattern the SIE should detect: when the Coach and/or Player cron jobs fail repeatedly, the entire autonomous development loop stalls — no reviews, no new tasks, no progress.

## Detection Heuristics

Add these to .learnings/ when the following conditions are observed:

- `cronjob list` shows coach-development-loop with `last_status: error` for 3+ consecutive ticks
- `cronjob list` shows player-development-loop with `last_status: error` for 3+ consecutive ticks
- Master checkpoint has `current_task: "tbd"` and `consecutive_on_project >= 10`
- Project AGENTS.md has 0 remaining tasks but user-facing gaps remain
- `vision_analyze` consistently fails (billing/rate-limit issue upstream)

## Scoring

This pattern should score highly because:
- `area: infra` (systemic dev loop issue)
- `recurrence: >= 3` (it recurs every tick)
- `priority: high` (blocks all autonomous progress)

## Mitigation Skills

When this pattern is detected, the SIE should consider:
1. Authoring a skill that checks cron health and auto-escalates
2. Adding a .learnings entry for the Coach/Player bottleneck cascade
3. Recommending model pinning (paid provider, not free-tier)
