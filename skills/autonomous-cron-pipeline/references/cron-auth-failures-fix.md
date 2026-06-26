# Cron Job Auth Fixer — Batch Repair Guide

**Date:** 2026-05-15  
**Problem:** All cron jobs using `provider: minimax-portal` fail at execution with `401 - login fail: X-Api-Key required`  
**Root cause:** Scheduler runs in different context than web UI — `minimax-portal` auth fails there, `custom` works in both

---

## Symptoms

- `cronjob action=list` shows many jobs with `last_status: error`
- Error: `RuntimeError: Error code: 401 - {'type': 'error', 'error': {'type': 'authentication_error', 'message': "login fail: Please carry the API secret key in the 'X-Api-Key' field of the request header"}`
- Jobs show `next_run_at` in the future (scheduler accepts them) but never succeed
- Discord delivery NOT the problem — failure is at model API authentication, before delivery is attempted

---

## Batch Fix Pattern

Find all jobs with `provider: minimax-portal` and `last_status: error`:

```python
# Jobs needing fix — list all cron jobs, filter by provider
jobs = [
    {"id": "56685e569e5f", "name": "Morning Briefing", "provider": "minimax-portal", "status": "error"},
    {"id": "6d747879c7c5", "name": "Cross-Agent Bridge Poll", "provider": "minimax-portal", "status": "error"},
    {"id": "33ee3807d679", "name": "hermes-sync rolling rebuild", "provider": "minimax-portal", "status": "error"},
    {"id": "4d2609ce31ba", "name": "agent-os-canary-watch", "provider": "minimax-portal", "status": "error"},
    {"id": "2c60270a3745", "name": "Hermes Full Backup — Git sync", "provider": "minimax-portal", "status": "error"},
    {"id": "ad90af79146c", "name": "Hermes Full Backup — Docker Image", "provider": "minimax-portal", "status": "error"},
]
```

Fix each: `cronjob action=update job_id=<id> model={"model": "MiniMax-M2.7"}` (omitting `provider` or setting to `custom`).

After fix, trigger a test run to confirm: `cronjob action=run job_id=<id>`.

---

## Why This Happens

| Provider | Endpoint | Auth | Works in web UI | Works in scheduler |
|----------|----------|------|-----------------|-------------------|
| `minimax-portal` | `https://api.minimax.io/anthropic` | `X-Api-Key` header | ✅ Yes | ❌ 401 |
| `custom` | `https://api.minimax.io/v1` with `anthropic_messages` mode | Bearer token | ✅ Yes | ✅ Yes |

The scheduler uses a different request-building path than the web UI session. `minimax-portal` wraps the Anthropic endpoint with `X-Api-Key` which the scheduler resolves incorrectly for the bot token context. `custom` uses the standard OpenAI-compatible endpoint with bearer auth, which works everywhere.

---

## Prevention

When creating ANY new cron job:
```python
cronjob action=create
    model={"model": "MiniMax-M2.7"}   # explicit model
    # provider: OMIT — let scheduler use its default
    # OR set provider="custom" explicitly
```

Never create cron jobs without an explicit `model`. Never use `minimax-portal` as a provider in cron job context.

---

## Jobs Fixed on 2026-05-15

| job_id | name | fix applied |
|--------|------|------------|
| `f5a499e5d25a` | hermes-web-computer: Phase Engine (60m) | provider → `custom`, deliver → `local` |
| `4d2609ce31ba` | agent-os-canary-watch | provider → `custom`, model explicit |