---
name: cron-job-optimization
description: Full audit and optimization of Hermes cron jobs — frequency reduction, redundancy detection (watchdog vs systemd), prompt fixes, toolset trimming, and delivery fixes.
---

# Cron Job Optimization

Run this when asked to "audit cron jobs", "optimize cron jobs", "fix cron schedules", or when cron bloat is suspected.

## Critical Rule — Investigate Before Proposing Deletions

**Do NOT propose deletions based on names, descriptions, or labels alone.** Every job was created for a reason, and the name may not reflect what it actually does. Always:

1. **Read the full prompt** — from `jobs.json`, not the truncated `cronjob(action='list')` preview
2. **Check the output history** — run count, silent ratio, output size, content patterns (see §3a)
3. **Verify cross-job overlap** — read two prompts side by side to confirm real redundancy
4. **Explain your reasoning first** — before making any change, present the evidence to the user and let them decide

**This is the single most important rule.** Presenting a list of candidates without evidence (run counts, silent ratios, output samples) will get corrected. The evidence must come first, the action second.

## Steps

### 1. Get Full Inventory
```
cronjob(action='list')
```
Note each job's: name, schedule, last_status, deliver field, enabled_toolsets, workdir, repeat count.

### 2. Read Full Prompts
Read `/home/hermeswebui/.hermes/cron/jobs.json` for each job's raw prompt text.

### 3. Audit Each Job Against These Criteria

**Redundancy:** Is the service it monitors already managed by systemd/host supervisor? If yes → the watchdog is informational only. Reduce frequency or convert to `no_agent: true`.

**Frequency:** Does it run more often than once per 15 minutes? → Usually excessive. Systemd handles crash recovery. Watchdog frequency should match the recovery window (every 15m for a service that recovers in seconds).

**Session bloat:** Each agent cron tick creates a full session in state.db. A 5-min watchdog = 288 sessions/day. Calculate annual session creation (tickers × 365).

**Error state:** Check `last_status: error` and `last_error`. Investigate individually.

**Delivery:** `deliver: origin` fails on cron jobs (no originating conversation). Always use `deliver: local`.

**Stale paths:** Check workdir and prompt paths against current filesystem. Reorganized projects (June 2026) moved repos out of /workspace/.

**Stale skill references:** Check `jobs.json` for any job that has `skills: ["<name>"]` where `<name>` doesn't exist in the skills directory. A job that references a deleted/nonexistent skill will still run (the prompt is inlined), but the cron system logs a warning every tick. Fix: set `skills: []` on update. Example: `master-development-loop` referenced `master-development` which never existed as a skill — clearing the ref stopped the warning spam.

**Toolset fit:** If a job only needs `terminal`, don't give it `[terminal, web]`. Fewer tools = less token overhead.

**Prompt quality:**
- Agent-mode monitoring jobs should have diagnostic value (not just "200 OK")
- Dev-maintenance jobs should pick ONE task per run, not scan everything
- Build-check jobs should use correct commands for the project type (go build vs npm run build)

### 3a. Evidence-Based Redundancy Quantification

Before deciding to delete or consolidate a job, **quantify** the actual redundancy by examining the job's output history. Don't rely on name/description alone — the output files tell the real story.

**1. Count total runs vs output size:**
```bash
ls /home/sc/.hermes/cron/output/<job-id>/*.md | wc -l
du -sh /home/sc/.hermes/cron/output/<job-id>/
```
High run count + large output dir + same output every time = strong consolidation signal.

**2. Measure silent ratio** (jobs with `[SILENT]` or conditional-reporting patterns):
```bash
grep -l 'SILENT' /home/sc/.hermes/cron/output/<job-id>/*.md | wc -l
```
A job that is **>95% silent over 100+ runs** is a deletion candidate. Example: auto-continue-work (152 runs, 100% silent — every single tick found nothing to do).

**3. Detect repetitive outputs** (health-check / watchdog jobs):
```bash
grep -r "healthy\|UP\|DOWN\|FAILED" /home/sc/.hermes/cron/output/<job-id>/*.md | \
  awk -F': ' '{print $2}' | sort | uniq -c | sort -rn | head -20
```
If the top 3-5 variants account for >90% of outputs and all say "healthy" or equivalent, the job has not produced actionable information for its entire history.

**4. Cross-job overlap check:** Read the raw prompts side by side:
```bash
jq '.jobs[] | select(.id == "<id>") | .prompt' /home/sc/.hermes/cron/jobs.json
```
Identify overlapping checks. If job A's every check is a subset of job B's broader scope, job A is a consolidation candidate. Example: GTO Watchdog (3 checks, all covered by GTO QA Sweep which adds courses data validation).

**5. Check for actual problem detection:**
```bash
cat /home/sc/.hermes/cron/output/<job-id>/$(ls -t /home/sc/.hermes/cron/output/<job-id>/*.md | tail -5 | head -1)
```
Scan recent outputs for evidence of catching real issues, not just "everything healthy." A job that has only ever reported healthy across 500+ runs is not providing value above a simple script.

**6. Historical spike check:** Cross-reference the output history with known incidents:
- Was the job reporting during outage periods?
- Did its output change color/tone when the service was actually down?
- Or did it keep reporting healthy while the service was broken (wrong endpoint)?

**Decision thresholds:**
| Metric | Threshold | Action |
|--------|-----------|--------|
| Silent ratio | >95% over 100+ runs | Delete — job has no value |
| Repetitive output | >90% identical over 500+ runs | Convert to no_agent or reduce frequency 10x |
| Full coverage by another job | 100% overlap | Delete — keep the broader job |
| Catches real issues | Any in last 30 days | Keep — has demonstrated value |
| Never caught an issue | Never in entire history | Strong prune candidate — the check pattern itself may be wrong |

### 4. Make Changes

Apply fixes via `cronjob(action='update', ...)` for each job:

```python
# Reduce frequency
cronjob(action='update', job_id='b664efd', schedule='*/15 * * * *')

# Fix deliver
cronjob(action='update', job_id='64280d3', deliver='local')

# Fix prompt
cronjob(action='update', job_id='ecb3846', prompt='...', workdir='...')

# Fix workdir
cronjob(action='update', job_id='4285b86', workdir='/correct/path')
```

### 5. Verify

Run each modified erroring job:
```python
cronjob(action='run', job_id='xxx')
```
Then `cronjob(action='list')` to confirm status.

## Common Patterns

| Pattern | Before | After | Savings |
|---------|--------|-------|---------|
| systemd-managed watchdog | every 5 min | every 15 min | ~67% fewer sessions |
| general auto-continue | every 30 min | hourly | ~50% fewer sessions |
| dead-end QA checking dead service | keep but add diagnostics | add binary-age + rebuild-needed checks | more useful |
| `deliver: origin` | silent failure | `deliver: local` | output visible |
| wrong build commands | `npm run build` on Go project | `go build ./...` | actual build verification |

## Pitfalls

- Don't reduce frequency so much that problems can slide unnoticed. Balance session/token savings with detection latency.
- `cronjob(action='run')` schedules the run — it takes one scheduler tick (~1 min) to fire.
- After workspace reorganization, ALL prompting paths must be re-validated.
- The Memory Curation job needs `search` and `file` toolsets, not `terminal`.
