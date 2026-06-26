# Cron Audit Case Study — June 2026

## Context

Review of 18 active cron jobs. Goal: identify redundancies, delete noise, consolidate overlapping jobs.

## Methodology Applied

1. **List all jobs** — `cronjob(action='list')`
2. **Read full prompts** — `read_file(~/.hermes/cron/jobs.json)` (raw JSON with complete prompt field)
3. **Quantify output** — for each candidate, checked output directory: file count, total size, content samples
4. **Measure silent ratio** — grep for `[SILENT]` across all output files
5. **Detect repetitive outputs** — grep unique variations of health-check verdicts
6. **Cross-job overlap** — compare prompts side by side for overlapping checks
7. **Check for actual value** — scan outputs for evidence of catching real problems

## Key Findings

### auto-continue-work — Hourly, 152 runs, 100% [SILENT]

**Evidence gathered:**
- `ls | wc -l` = 152 output files
- `grep -l 'SILENT' | wc -l` = 152 (100% silent)
- Checked early, middle, and late outputs — all `[SILENT]` or equivalent
- The daily Cron Health Check covers all the same monitoring ground

**Decision:** Delete. 152 consecutive silent runs is definitive — the job has never found anything worth reporting. Its tasks (GTO health, port scan, disk check) are covered by other jobs that run less frequently.

### GTO Watchdog — Every 15min, 576 runs, 2.3MB

**Evidence gathered:**
- 576 output files in 14 days (~41/day)
- `grep` unique variants: 409 say "healthy" in one form or another
- Only ~5 actual failure events out of 576 runs
- The GTO QA Sweep (every 2h) checks ALL the same endpoints PLUS courses data integrity

**Decision:** Delete in favor of keeping the GTO QA Sweep (broader scope, actual data validation). Reduce QA Sweep to hourly.

### HWC Jobs — 4 overlapping for one project

**Evidence gathered:**
- Canary Watch (3x daily): curl /health + curl / — same as Visual QA
- Visual QA (every 12h): same checks + binary freshness — but mostly [SILENT] because Canary already reported
- Nightly Build Health (daily): git status + binary date vs commit date — found binary name mismatch (`myserver` vs `agent-os`)
- Rebuild + Deploy Check (2x daily): only build-test job — last run errored (provider issue, not code)

**Decision:**
- Delete 3 health-check jobs (Canary, Visual QA, Nightly Build) — merge into one daily Health Audit
- Keep Rebuild + Deploy Check as the only build-test job, add a health line to its report

### master-development-loop — Every 2h, 6 runs

**Evidence gathered:**
- Workdir `/workspace` doesn't exist on host
- SSH path uses wrong IP and key path (`sc@172.19.0.1` with key at non-existent path)
- Skill `master-development` doesn't exist (related skill `master-skill` is an unrelated stub)
- Deliver `origin` always fails
- **BUT** checkpoint file exists at `~/.hermes/master-checkpoint.json` with real project data
- Last run: committed 6 files to energy-aware-task-router (Phase 4a, 32 tests pass)

**Decision:** Fix, don't delete. The job is producing real work despite being theoretically broken. The SSH from container uses agent forwarding which bypasses the documented key path. Fix: correct workdir, delivery, and make prompt self-contained (don't reference missing skill).

### auto-continue-work — Deeper Analysis

The prompt tells it to pick ONE of 4 tasks per run, and to respond `[SILENT]` if everything is healthy. Over 152 consecutive hours (6+ days), everything was always healthy. This is the strongest possible signal that the job provides no value at its current frequency and scope.

## Decision Summary

| Job | Runs | Verdict | Rationale |
|-----|------|---------|-----------|
| auto-continue-work | 152 | Delete | 100% silent — no value |
| GTO Watchdog | 576 | Delete | Redundant with QA Sweep |
| GTO QA Sweep | 5 | Keep & extend | Broader scope, data validation |
| HWC Canary Watch | 75 | Delete | Merged into daily health audit |
| HWC Visual QA | 7 | Delete | Merged into daily health audit |
| HWC Nightly Build | 16 | Delete | Merged into daily health audit |
| HWC Rebuild | 63 | Keep & enhance | Only build-test job |
| master-development-loop | 6 | Fix | Producing real work despite broken config |
| context-budget-audit | 1 | Fix | deliver=origin → deliver=local |

## Lessons

1. **Output files are the truth.** A job's `last_status` only tells you if the agent exited cleanly, not whether the output was useful. Always inspect actual output content.
2. **Silent ratio is the strongest deletion signal.** A job designed to report only on problems that never occur is a job that should not exist. If 100+ silent runs can be verified, the monitoring need is not real.
3. **Cross-job overlap is common** when projects grow organically. Always compare prompts side by side — the names may suggest different purposes but the checks may be identical.
4. **"Broken but working" happens.** SSH from container uses agent forwarding, not key files. The documented SSH paths in skill references may be stale while the actual mechanism works perfectly. Check runtime behavior, not just documented config.
5. **Evidence beats instinct.** Without counting output files and measuring silent ratios, the instinct would have been "hourly auto-continue seems reasonable." The data showed it was pure waste.
