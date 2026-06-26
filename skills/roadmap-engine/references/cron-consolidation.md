# Cron Job Consolidation — Lessons from May 2026 Overhaul

## Problem
35 cron jobs, most failing. Root causes:
- Default model `opencode-go/deepseek-v4-flash` had no API key in container
- Jobs referenced stale paths from host perspective
- Multiple overlapping jobs for same project phases
- Discord-dependent jobs without Discord token in container
- Phase engine jobs running after all phases complete

## Solution: Unified Pipeline Pattern

Replace N fragmented jobs with 1 coordinated pipeline:

**Before** (14 jobs for GTO + HWC + monitors):
- GTO Phase A, B, C, D, E (5 phase-specific jobs)
- GTO Phase 1, 2, 3, 4+5+6, E2E (5 execution jobs)
- GTO Progress Monitor (1)
- HWC v1.3 Phase Engine, Phase Engine resume, Visual QA, canary watch, rebuild+deploy, nightly build health (6)
- Cross-Agent Bridge, Delegation Monitor, Autonomy Digest, System Monitor (4)

**After** (1 coordinated pipeline + 2 GTO + 3 HWC):
- Nightly OWL Alpha Dev Pipeline (checks ALL projects sequentially)
- GTO Phase 2 Variant Polish (kept — works, focused)
- GTO Phase 4+5+6 Final Polish (kept — works, focused)
- HWC canary watch, rebuild+deploy, nightly build health (kept — infrastructure)

## Key Decisions

1. **All jobs use same model** (`openrouter/owl-alpha`) — no more provider fragmentation
2. **Model set explicitly on each job** — don't rely on default from config.yaml
3. **Paths verified in container** — `/opt/data/<project>/` not `/home/hermeswebui/.hermes/`
4. **Project retirement** — when all phases complete, remove the phase engine jobs
5. **Discord jobs removed** — token not available in container, would need host execution

## Job Count: 35 → 15 (57% reduction)

## Schedule for Nightly Pipeline

Sydney overnight (1am-7am) = UTC 15:00-21:00:
- `0 15,17,19,21 * * *` — 4 runs, every 2 hours
- Each run checks all projects, does what it can, commits/pushes
- Delivers report to origin (Sean's chat)
