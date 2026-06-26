# Cron Job Management — Patterns & Pitfalls

## Common Failure Modes

### 1. "No models provided" (HTTP 400)
Fix: Set `model: "owl-alpha"` + `provider: "openrouter"`.

### 2. "Connection error" (OpenRouter)
Cause: Model string doesn't match provider. When provider=openrouter, model must be bare name (e.g., "owl-alpha"), NOT "openrouter/owl-alpha" or "deepseek-v4-flash".
Root cause: The `update` API changes provider but does NOT rewrite the existing model string.
Fix: When changing provider, ALWAYS also set model explicitly.

### 3. `jobs.json` Permission Denied
Cause: File written from root-owned sandbox, cron runs as hermes (uid 1000).
Fix: `chown hermes:hermes /opt/data/cron/jobs.json`. Prefer `hermes cron` CLI over direct file writes.

### 4. `deliver: origin` Fails in Cron Container
Cause: Cron container has no origin chat context. Error: "no delivery target resolved".
Fix: Use `deliver: local` for all cron jobs.

### 5. "Insufficient credits" (HTTP 402) — NOT a rate limit
Cause: OpenRouter account-level credit exhaustion. Different from HTTP 429 (rate limit).
402 = "no money in account". 429 = "too many requests, slow down".
Fix: Add credits at https://openrouter.ai/settings/credits. Retrying won't help until credits are added — this is NOT a transient error.

### 6. `cronjob run` is asynchronous
The command returns immediately with the job config. Job runs in background, writes output to `/opt/data/cron/output/<job_id>/`. Poll via `cronjob list` (check `last_run_at`, `last_status`) or watch the output directory. Running `cron run` does NOT reset the repeating counter — it fires an extra execution on top of scheduled runs.

### 7. Wrong model string survives provider change
`cronjob update` changes `provider` and `model` independently. If you set `provider: "openrouter"` but forget to change `model: "deepseek-v4-flash"` to `model: "owl-alpha"`, the old model string is kept. ALWAYS update both fields in the same call. Verify with `cronjob list` after updating.

## Cron Job Lifecycle

1. **Create** → `cronjob create` with prompt, schedule, model, provider, deliver
2. **Verify** → `cronjob list` shows correct config, check next_run_at
3. **First run** → `cronjob run <id>` to trigger immediately (async)
4. **Debug** → check `/opt/data/cron/output/<id>/` for output .md files
5. **Remove** → `cronjob remove <id>` when project phase complete or job persistently fails

**Removal criteria**: Project complete (no pending phases), job failing >7 runs with same error, required resources unavailable (Discord token, host-only scripts), or skill dependencies not installed.

## Schedule Convention

**Default: Sydney overnight (midnight-7am AEST = 14:00-21:00 UTC)**.
AEDT (summer): use 13:00-20:00 UTC instead.

Exceptions (outside overnight window): Morning Briefing (21:30 UTC weekdays), seans-reporepo (Mon 09 UTC), html-in-canvas (Mon 09 UTC), context-budget-audit (1st 09 UTC), skill-selector-prep (Sun 06 UTC).

## Active Jobs (2026-05-30)

All: model=owl-alpha, provider=openrouter, deliver=local.
Nightly OWL Alpha Pipeline: 14,16,18,20 UTC | Roadmap: 14,17,20 | HWC canary: 14,18,22 | HWC rebuild: 16,20 | HWC health: 19 | GTO P2: 15,19 | GTO P4+5+6: 16,20 | Backup Git: 14,18,22 | Backup Docker: 17 | Memory: 16 | seans-reporepo: Mon 09 | html-in-canvas: Mon 09 | context-audit: 1st 09 | skill-prep: Sun 06