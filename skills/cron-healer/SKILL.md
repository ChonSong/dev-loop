---
name: cron-healer
description: How the cron-healer system works — programmatic no-LLM fallback for failing cron jobs
---

# Cron Healer System

A `no_agent` cron job that programmatically switches models on erroring LLM cron jobs. Zero LLM calls — pure Python, direct `jobs.json` manipulation, Discord bot API notification.

## Architecture

**Healer job** (`no_agent: true`, runs every 2h):
- Script: `~/.hermes/scripts/cron-healer.py`
- Reads `~/.hermes/cron/jobs.json` directly
- Tracks consecutive failures in `~/.hermes/cron/heal-history.json`
- Escalates only after 2+ consecutive errors
- Writes model changes directly to `jobs.json`
- Notifies via Discord Bot API (uses `DISCORD_BOT_TOKEN` + `DISCORD_HOME_CHANNEL` from `.env`)

**Fallback chain (per model):**
```
deepseek-v4-flash-free  → openrouter/owl-alpha → deepseek-v4-flash
openrouter/owl-alpha    → deepseek-v4-flash    → deepseek-v4-flash-free
deepseek-v4-flash       → deepseek-v4-flash-free
```

## Files

- `~/.hermes/scripts/cron-healer.py` — the script
- `~/.hermes/cron/jobs.json` — read/written directly by script
- `~/.hermes/cron/heal-history.json` — consecutive failure tracking (auto-created)
- `~/.hermes/logs/cron-healer.log` — run log

## Key design decisions

1. **no_agent = true** — pure script, no LLM calls. Works even when all models are rate-limited.
2. **2-consecutive-failure threshold** — prevents premature escalation on jobs that just haven't run yet under the new model.
3. **Direct jobs.json manipulation** — bypasses the `hermes cron edit` CLI (which lacks `--model`/`--provider` flags).
4. **Discord bot API** for notification (not webhook) — uses existing `DISCORD_BOT_TOKEN` from `.env`.
5. **Jobs with null model are skipped** — they use the system default provider, not pinned to a specific model.

## Creating a new healer job

```bash
cronjob(action='create', 
  name='cron-healer',
  schedule='0 */2 * * *',
  script='cron-healer.py',
  no_agent=true,
  deliver='local')
```

## Hermes built-in alternative

Hermes has `fallback_providers` config option for cross-provider failover at the agent level (not per-cron-job):
```yaml
fallback_providers: ["openrouter"]
fallback_model: "openrouter/deepseek/deepseek-chat"
```
But this affects the main session, not individual cron jobs. The cron-healer handles per-job model switching.
