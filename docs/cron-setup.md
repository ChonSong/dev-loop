# Cron Job Setup

Two cron jobs drive the dev loop. A third handles ongoing monitoring.

## Player Cron

Runs every hour, implements one task from the backlog.

| Field | Value |
|-------|-------|
| **Name** | `player-development-loop` |
| **Schedule** | `0 * * * *` (every hour at :00) |
| **Skills** | `["player-agent"]` |
| **Model** | Flash/cheap (`deepseek-v4-flash` via `opencode-go`) |
| **Toolsets** | `["terminal", "file", "web"]` |
| **Deliver** | `origin` (back to WebUI) |

```bash
hermes cron create \
  --name "player-development-loop" \
  --schedule "0 * * * *" \
  --prompt "Execute the player-agent role. Read master checkpoint, find the next pending task, implement it, test, commit, and push." \
  --skills "[\"player-agent\"]" \
  --model "{\"provider\":\"opencode-go\",\"model\":\"deepseek-v4-flash\"}" \
  --enabled-toolsets "[\"terminal\",\"file\",\"web\"]"
```

## Coach Cron

Runs 5 minutes after the Player. Reviews the last commit and checks backlog health.

| Field | Value |
|-------|-------|
| **Name** | `coach-development-loop` |
| **Schedule** | `5 * * * *` (every hour at :05) |
| **Skills** | `["coach-agent"]` |
| **Model** | Same as Player (reliability > separation) |
| **Toolsets** | `["terminal", "file"]` |
| **Deliver** | `origin` |

```bash
hermes cron create \
  --name "coach-development-loop" \
  --schedule "5 * * * *" \
  --prompt "Execute the coach-agent role. Review the last player commit, verify against AGENTS.md criteria, and output DECISION: APPROVE/FIX/REVERT. Then check backlog health and generate tasks if needed." \
  --skills "[\"coach-agent\"]" \
  --enabled-toolsets "[\"terminal\",\"file\"]"
```

## Memory Curation Cron

Daily audit of all projects. Flags stalled tasks, evaluates coach quality.

| Field | Value |
|-------|-------|
| **Name** | `memory-curation` |
| **Schedule** | `0 16 * * *` (daily at 4pm) |
| **Toolsets** | `["search", "file", "terminal"]` |
| **Deliver** | `origin` |

## Cron Management Notes

- Use `hermes cron list` to see all jobs
- Use `cronjob(action='list')` to inspect job details
- Use `cronjob(action='update', job_id='...', model={...})` to change model
- Use `cronjob(action='pause', job_id='...')` to pause without deleting
- If a job errors repeatedly (HTTP 429, provider error), update the model to a reliable fallback
- All paths in cron prompts must be reachable from the cron runtime environment
