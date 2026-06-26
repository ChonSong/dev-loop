# Roadmap Autonomy Engine — Updated (May 18, 2026)

> **Source:** `workspace/plans/roadmap-engine-spec.md` in hermes-sync
> **Status:** Active — Phase 1+2+3 fully operational

## Quick Reference

Long-horizon autonomous planning and execution system:

1. Revises a persistent `roadmap.json` each night (top-down goals + bottom-up discovery)
2. Executes tasks across 5 dimensions: tests_passing, design_quality, user_experience, autonomous_simulation, research_discovery
3. Reports to morning briefing with carry-forward tracking

## Key Updated Facts (vs legacy spec)

| Setting | Old (Stale) | Current (Correct) |
|---------|-------------|-------------------|
| Hermes binary | `/opt/hermes/.venv/bin/hermes` | `/home/sean/.hermes/hermes-sync/.venv/bin/hermes` |
| Python in venv | `/opt/hermes/.venv/bin/python` | `HERMES_SYNC / ".venv/bin/python"` |
| venv path | `/opt/hermes/.venv/` | `/home/sean/.hermes/hermes-sync/.venv/` |
| hermes version | unknown | v0.12.0 (2026.4.30), Python 3.13.11 |
| ruff | not installed | v0.15.13, auto-fix mode (`--fix --unsafe-fixes`) |
| workspace/projects | not symlinked | symlink → `../projects` (resolves to `hermes-sync/projects/`) |
| openclaw project | active (14 tasks) | blocked — `ChonSong/openclaw` repo doesn't exist |

## Directory Structure

```
hermes-sync/scripts/
├── roadmap_engine.py    # Main entry point (Phase 1+2+3 runner) — PRIMARY
├── roadmap.py            # Data model + roadmap CRUD
├── reporters.py           # Phase 3 narrative report generator
├── planner.py             # LLM-driven task planning
├── executor.py            # Task execution (test, code, research, browser, review)
├── research.py            # Discovery-driven bottom-up idea generation
└── self_improvement.py    # Self-improvement loop entry point
```

```
hermes-sync/workspace/plans/
├── roadmap.json           # Single source of truth (seeded with 5 projects)
└── roadmap-history/       # Per-session snapshots
```

## Task Types (Executor)

| Type | Status | Approach |
|------|--------|----------|
| `test` | ✅ Working | Run pytest in repo; if 0 tests collected, spawn coder subagent |
| `code` | ✅ Working | TDD cycle: write tests → hermes chat coder → apply diff → commit |
| `research` | ✅ Working | Spawn hermes chat with web toolset; findings saved to plans/research-* |
| `browser` | ✅ Working | Spawn hermes chat -t browser for web automation tasks |
| `review` | ✅ Working | Spawn hermes chat; review saved to plans/review-* |

## Phase Cycle

```
Phase 1 RESEARCH (30-60 min):
  Clone/pull repos → scan TODOs/FIXMEs → GitHub issues → CI failures
  → self-improvement scan (learnings → high-priority skill candidates)
  → LLM planner revises roadmap.json → snapshot to roadmap-history/

Phase 2 EXECUTE (until 14:00 UTC / midnight Sydney):
  Load top tasks → verify preconditions → execute via appropriate executor
  → record results → update roadmap → commit hermes-sync changes
  → lint gate: ruff check --fix --unsafe-fixes before commit (or --skip-lint bypass)

Phase 3 REPORT (15-30 min):
  Generate narrative report → critical issues to Telegram → rest to morning briefing
  → push roadmap.json + report to git
```

## Known Issues

- `repo-transmute` pytest test discovery: `pyproject.toml` configures `tests/` but pytest not discovering
- `ChonSong/openclaw` GitHub repo doesn't exist — all 14 openclaw tasks blocked via proj-005 status='blocked'
- Phase 1 planner (line ~183) may overwrite roadmap.json with minimal version — `Roadmap.save()` itself is NOT the wipe cause

## Running

```bash
# Production (with lint gate)
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 \
  "cd /home/sean/.hermes/hermes-sync && python scripts/roadmap_engine.py --phase all"

# Development (skip lint gate)
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 \
  "cd /home/sean/.hermes/hermes-sync && python scripts/roadmap_engine.py --phase all --skip-lint"
```

**hermes-sync root:** `/home/sean/.hermes/hermes-sync/`
**venv:** `/home/sean/.hermes/hermes-sync/.venv/`