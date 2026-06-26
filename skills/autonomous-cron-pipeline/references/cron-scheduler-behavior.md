# Hermes Cron Scheduler Behavior

> Observed failures and working patterns from May 2026 sessions

## One-Shot Jobs Are Unreliable

**Pattern:** `schedule: "once at 2026-05-12 04:00:00"` with `repeat: "once"`

**Problem:** The scheduler only fires if the tick catches the exact scheduled time. If:
- Agent was restarting at that moment
- Tick missed by even 1 minute
- Job created with time already in past relative to scheduler check

...the job shows `next_run_at: null` and NEVER fires.

**Evidence from May 2026:**
- Phase L scheduled for 04:00 UTC → `next_run_at: null`, `last_run_at: null`
- Phase M scheduled for 04:15 UTC → same
- By 07:32 UTC, all 4 phases (L, M, N, O) had never run
- Had to force-trigger all 4 with `cronjob action=run`

## The ONLY Reliable Pattern

**Recurring job with state file check:**
```yaml
name: "phase-engine: project completion"
schedule: "every 30m"          # NOT "once at <timestamp>"
repeat: 10                     # Max runs (safety limit)
deliver: "discord"
enabled_toolsets: ["terminal", "file"]
prompt: |
  Read /opt/data/project-state/<project>/PHASE_TRACKER.json
  Find first phase with status != "complete"
  Execute it, verify, commit, write checkpoint, update tracker
```

**Why this works:**
- Even if a tick is missed, next run picks up where it left off
- State is on disk (JSON file), not in memory
- Each phase commits independently to GitHub

## Force-Run as Fallback

If you MUST use one-shot jobs:
1. Create the job
2. IMMEDIATELY force-run: `cronjob action=run job_id=<id>`
3. Verify `next_run_at` is not `null`
4. Don't rely on scheduler to catch the time

## Scheduler Tick Frequency

Unknown exact frequency, but observed behavior suggests:
- Ticks are NOT continuous
- One-shot jobs require the tick to align with the scheduled time
- If the window is missed, the job is silently skipped

## State Verification Before Scheduling

Before creating any cron jobs for phases:
```bash
cd <project> && git log --oneline -10 && git status
```

This prevents scheduling cron jobs for phases that are already committed (a trust-eroding mistake observed in May 2026 sessions).
