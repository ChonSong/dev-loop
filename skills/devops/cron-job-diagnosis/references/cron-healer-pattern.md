# Cron Model Fallback Healer Pattern

## Problem
Cron jobs using LLM models can fail when the model provider has issues (rate limits, downtime, quota exceeded). When a job's model breaks, the job stops making progress until a human notices and fixes it.

## Solution: Cron Healer
A lightweight cron job that:
1. Lists all cron jobs (via `cronjob` tool)
2. Identifies jobs where `last_status == "error"` and `model` is not null
3. Switches erroring jobs to a fallback model
4. Notifies via Discord

## Model Fallback Map
```
deepseek-v4-flash (opencode-go) → openrouter/owl-alpha (openrouter)
openrouter/owl-alpha (openrouter) → deepseek-v4-flash (opencode-go)
```

## Known Reliable Models (as of 2026-06)
- `openrouter/owl-alpha` — reliable, used by Memory Curation (always succeeds)
- `deepseek-v4-flash` via `opencode-go` — works intermittently, errors often

## Healer Cron Job
- **Name**: cron-healer
- **Schedule**: Every 2 hours (`0 */2 * * *`)
- **Model**: `openrouter/owl-alpha` (use the most reliable model for the healer itself)
- **Tools**: `cronjob`, `send_message` (for Discord notification)
- **Job ID**: `4961f5714c31`

## Deploy Script Blind Spot
The GTO Wizard deploy script (`deploy.sh`) does `git fetch` then compares local HEAD to remote. If they match (because the user pushed from the same machine), it says "Already up to date" and **skips the build**. This means:
- Pushing from the local repo → deploy script won't rebuild
- Must manually run `npx turbo build --force` and `systemctl --user restart gto-wizard-web.service`
- Or wait for the next remote push from a different machine
