# Cron Model Fallback Strategy

## Problem
Free-tier LLM models (e.g., `deepseek-v4-flash` via `opencode-go`) rate-limit with HTTP 429 errors. When a cron job's model rate-limits, the job fails silently until the next day.

## Solution: Cron Healer Pattern

A dedicated cron job (`cron-healer`) runs every 2 hours and:
1. Lists all cron jobs
2. Identifies erroring LLM jobs (last_status=error, model is not null, not no_agent)
3. Switches erroring free-tier jobs to paid fallback
4. Switches erroring paid-tier jobs back to free (recovery attempt)
5. Sends Discord notification about changes

## Model Tiers

| Tier | Provider | Model | Cost | Reliability |
|------|----------|-------|------|-------------|
| Free | opencode-go | deepseek-v4-flash | Free | Rate-limited |
| Paid | openrouter | openrouter/owl-alpha | Credits | Reliable |

## Error Signatures

- `HTTP 429` — rate limit, switch to paid
- `Provider returned error` — provider down, switch to other provider
- Empty response / timeout — may be rate limit or provider issue

## Key Rules

- **Never leave a job at null model** — it errors every run
- **Prefer free tier** — only escalate to paid when free is actually erroring
- **Recovery** — if paid tier also errors, try free again (rate limit may have cleared)
- **Notify** — always send Discord message so user knows what changed
- **Conservative** — only switch on `last_status: error`, not on transient issues
