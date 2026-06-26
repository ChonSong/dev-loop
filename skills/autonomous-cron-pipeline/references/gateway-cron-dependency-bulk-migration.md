# Gateway ↔ Cron Dependency & Bulk Model Migration

> Observed May 2026 — Hermes WebUI container, single-instance architecture

## Gateway Dependency

Cron jobs do **not** fire autonomously. They require `hermes gateway` running as a background process. The `hermes cron status` command checks for a live gateway process.

**In the WebUI container:** The gateway is NOT auto-started with the WebUI server. The WebUI (`server.py`) is the only Hermes process. To get cron firing:

1. Start the gateway: `hermes gateway` (background process)
2. Verify: `hermes cron status` → shows `✓ Gateway is running — cron jobs will fire automatically`
3. The `hermes` CLI must be in `$PATH` — in the WebUI container it's at `/home/hermeswebui/.hermes/home/.local/bin/hermes`

**Single-instance constraint:** The WebUI container runs exactly one Hermes instance. Do NOT start a separate gateway process — the container architecture means cron scheduling may need to be handled differently, or the gateway started alongside the WebUI.

## Stale State Detection

The file `~/.hermes/gateway_state.json` can show `gateway_state: "running"` with a **stale PID** from container boot. This file is not auto-cleaned when the process dies. To verify actual liveness:

```
hermes cron status   # shows ✓ or ✗ regardless of state file
```

If `hermes cron status` says `✗ Gateway is not running`, the state file is stale. Trust `cron status`, not the state file.

## Bulk Model Migration Pattern

When switching all cron jobs from one model/provider to another (e.g., MiniMax-M2.7 → opencode-go/deepseek-v4-flash):

1. **List all jobs**: `cronjob action=list` — note which have explicit model overrides (not `model: null`)
2. **Identify targets**: Only jobs with a set model need updating. Jobs with `model: null` inherit the system default.
3. **Update all in parallel**: All cronjob updates are independent — fire them simultaneously:
   ```
   cronjob action=update job_id=<id1> model={"model":"deepseek-v4-flash","provider":"opencode-go"}
   cronjob action=update job_id=<id2> model={"model":"deepseek-v4-flash","provider":"opencode-go"}
   ...
   ```
4. **Skip correctly**: Do NOT update:
   - Jobs with `model: null` (inherit default)
   - `no_agent: true` jobs (script-only, no LLM involved)
5. **Verify**: Re-list to confirm all model fields changed

**Real example (May 28, 2026):** 29 cron jobs total → 18 needed updating (had MiniMax-M2.7 or mini-max/M2.7), 11 already used default model, 2 were `no_agent: true` script-only jobs.

## Diagnostics Flow

When a user reports "I didn't receive a cron job delivery":

1. `hermes cron status` — is the gateway running? If ✗, that's the root cause.
2. `cronjob action=list` — check the specific job's `last_run_at`, `last_status`, `next_run_at`
3. If gateway IS running but job has `last_status: error`, the model call failed — check model/provider settings
4. If job ran successfully (`last_status: ok`) but user didn't receive it — check `deliver` target
