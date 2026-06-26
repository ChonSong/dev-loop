# Cron Job MiniMax 404 — Root Cause Analysis (May 2026)

## Symptom

All cron jobs with `provider=custom` fail with:
```
RuntimeError: HTTP 404: 404 page not found
```

The same API key works in interactive gateway sessions (99% cache hit rate) but fails in cron sessions.

## Root Cause

**`provider=custom` routes differently than `provider=minimax`.**

The `config.yaml` has:
```yaml
model:
  base_url: https://api.minimax.io/v1
  provider: custom
  api_key: sk-sp-djI...
```

When the **gateway** handles an interactive session, it uses the full `minimax` provider flow (including session/auth context) and works fine. When the **cron scheduler** calls `run_agent.py` directly (no gateway session), it uses the `custom` provider profile, which bypasses the working auth flow and hits a different MiniMax endpoint path that returns 404.

In contrast, `provider=minimax` uses the credential pool and proper MiniMax auth headers that work in both contexts.

## Affected Jobs

All jobs with `provider=custom` in cron/jobs.json:
- Morning Briefing (56685e569e5f)
- Cross-Agent Bridge Poll (6d747879c7c5)
- hermes-sync rolling rebuild (33ee3807d679)
- Hermes Full Backup × 2 (2c60270a3745, ad90af79146c)
- Roadmap Autonomy Engine (6576b5f87515) — **no provider set** (uses default)
- agent-os-canary-watch (4d2609ce31ba)
- hermes-web-computer: Phase Engine (85d63c9f073a)

Jobs WITHOUT explicit `provider=custom` (e.g., Memory Curation, System Monitor) also fail with 404 — likely because the main config defaults to `provider: custom`.

## Verification

From the log, successful calls use:
```
provider=minimax in=100021 out=256 ... cache=99529/100021 (100%)
```

Failing calls use:
```
provider=custom model=MiniMax-M2.7 ... HTTP 404: 404 page not found
```

## Fix

Change all cron jobs from `provider=custom` to `provider=minimax`.

In `~/.hermes/cron/jobs.json`, for each job with `"provider": "custom"`:
```json
"provider": "minimax"
```

Then resume the jobs via `cronjob action=resume job_id=<id>`.

## Why `provider=minimax` Works

The `minimax` provider profile (defined in `model_metadata.py`) uses the provider's canonical auth headers and endpoint routing. The `custom` profile is a generic OpenAI-compatible wrapper that doesn't apply MiniMax-specific auth.

## Note on API Keys

The `config.yaml` contains `api_key: sk-sp-...` and `.env` contains `MINIMAX_API_KEY=sk-cp-...` — different key types. The `sk-sp` key works through the gateway/minimax provider but not via direct API. This is a routing/auth context difference, not a key validity issue.

## Related

- `references/minimax-httpx-404-debug.md` — general MiniMax httpx 404 diagnostic approach
- `references/minimax-api-failures.md` — model error 1211 and other MiniMax failures