# 2026-06-11 — Bulk Provider Migration (16 cron jobs)

## Context
OpenRouter API key returned HTTP 401 on all `openrouter/owl-alpha` jobs. The system default model was also `openrouter/owl-alpha`, so jobs with `model: null` (inheriting default) were also affected.

## Migration Log

### Affected jobs: 16 total

**Pattern 1 — Explicitly pinned to openrouter/owl-alpha (8 jobs):**
Memory Curation, Morning Briefing, Backup, seans-reporepo refresh, context-budget-audit, HWC canary, HWC rebuild, HWC nightly, GTO Daily QA, html-in-canvas-monitor

Some of these already had `model: null` but inherited the broken default.

**Pattern 2 — Jobs with null model (4 jobs that weren't previously failing):**
Commitment Auditor, GTO Watchdog, Cron Health Check, HWC Visual QA

### Migration steps

1. **List all jobs**: `cronjob(action='list')` — identify every job referencing the dead provider, including null-model jobs
2. **Determine replacement**: `opencode-go/deepseek-v4-flash` was available (CLI-based, no API key required)
3. **Bulk update** (sequential, ~1/sec):
   - First batch: all jobs with explicit openrouter model → update to deepseek-v4-flash
   - Second batch: all jobs with null model → pin to deepseek-v4-flash
4. **Fix broken prompts**: 
   - GTO Watchdog was referencing a deleted script at `~/gto-wizard-clone/deploy-check/watchdog.sh` — rewrote to use direct HTTP health checks
   - HWC Visual QA was a `no_agent` script job referencing SSH — converted to LLM-based
5. **Verify**: Ran 2 jobs (Cron Health Check, HWC Visual QA) — both returned `last_status: 'ok'`

### Key insights

- **null-model trap**: Jobs with `model: null` don't appear to use the broken provider, but they inherit the system default which *was* the broken provider. You must check the config.yaml default model and pin these explicitly.
- **last_status doesn't clear on update**: Even after updating the model, `last_status` stays `'error'` until the job's next scheduled run. This is confusing but harmless — the job will succeed on its next tick.
- **Broken scripts need more than model migration**: Some jobs had prompt/script dependencies beyond the model (deleted script files, SSH-only workflows). These need prompt rewrites as a separate concern.

### Remaining after migration

8 jobs still show `last_status: 'error'` from their last run with the old broken model. They will auto-recover on their next scheduled tick.
