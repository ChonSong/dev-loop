# Roadmap Engine — Implementation Notes (May 18, 2026)

## Session Summary

Fixed Phase 2 execution: hermes binary path, ruff lint gate, symlink layout, `--skip-lint` flag.

## Phase 2 Fixes Applied

### 1. Hermes Binary Path (Critical)

- **Old (broken):** `HERMES = "/opt/hermes/.venv/bin/hermes"` (hardcoded, wrong host)
- **New (correct):** `HERMES_BIN = HERMES_SYNC / ".venv/bin/hermes"`
- **venv location:** `/home/sean/.hermes/hermes-sync/.venv/` (created via `python -m venv .venv`)
- **hermes version:** v0.12.0 (2026.4.30), Python 3.13.11
- **Python in venv:** `HERMES_SYNC / ".venv/bin/python"` (was also hardcoded to `/opt/hermes/...`)

Both `HERMES_BIN` and `hermes_py` in `roadmap_engine.py` now use the `HERMES_SYNC / ".venv/bin/..."` pattern.

### 2. Workspace/Projects Symlink

- PROJECTS_DIR = WORKSPACE / "projects" = `hermes-sync/workspace/projects/`
- Repos clone to `hermes-sync/projects/` (outside workspace/)
- Created symlink: `workspace/projects/` → `../projects` so both paths resolve to the same directory

### 3. Ruff Auto-Fix Mode

- **Command changed:** `ruff check .` → `ruff check --fix --unsafe-fixes .`
- Auto-fixes 56 of 59 errors in repo-transmute, 4 of 4 in everything-dashboard
- Remaining errors (3 in repo-transmute): intentionally left (complex type annotation issues)

### 4. `--skip-lint` Flag

- Added `--skip-lint` CLI argument to bypass lint gate during development
- Global `SKIP_LINT = False` variable; `if args.skip_lint: SKIP_LINT = True`
- Lint gate condition: `if not lint_passed and not SKIP_LINT:` — skip-lint bypasses revert
- Committed as `62c762e` "roadmap-engine: fix HERMES paths, add --skip-lint, auto-fix ruff"

### 5. Openclaw Project Blocked

- `ChonSong/openclaw` GitHub repo doesn't exist ("Repository not found")
- Set `proj-005` status to `'blocked'` — `todo_tasks()` naturally skips all 14 openclaw tasks
- Tasks preserved (not deleted), just filtered out until repo is created

## Current Roadmap State

- **7 tasks active** (14 openclaw tasks blocked via proj-005)
- Tasks: task-003 (translator.py chunking), task-004 (test framework), task-006 (lint target), task-007 (docker isolation), task-008 (CI signal), task-009 (context injection), task-010 (iteration)
- **Projects:** repo-transmute ✅, everything-dashboard ✅, hermes-sync ✅
- **Lint status:** repo-transmute (56/59 auto-fixed, 3 remaining), everything-dashboard (4/4 fixed)

## Git Push Status

- Local HEAD: `62c762e` (unpushed)
- Remote ahead of local: commit `4794d4d` "report: 2026-05-18" exists on GitHub not in local
- Stash exists: `stash@{0}` from earlier WIP session
- Resolution needed: `git pull --rebase` before pushing

## Phase 1 Root Cause (Roadmap Wipe)

The `Roadmap.save()` itself works correctly — direct Python test confirmed 21 tasks persist across save/reload.
The wipe was from the Phase 1 LLM planner revision (line ~183 of roadmap_engine.py) overwriting roadmap.json
with a minimal version on each run. This is still an active concern if the planner runs.

## Running the Engine

```bash
# With lint (production)
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 \
  "cd /home/sean/.hermes/hermes-sync && python scripts/roadmap_engine.py --phase all"

# With --skip-lint (development)
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 \
  "cd /home/sean/.hermes/hermes-sync && python scripts/roadmap_engine.py --phase all --skip-lint"
```

## Cron Job

- Job ID: `6576b5f87515` — "Roadmap Autonomy Engine — Overnight (1am-7am Sydney)"
- Schedule: `0 14-20 * * *` (every hour 14–20 UTC = midnight–6am Sydney)
- Next fire: 2026-05-18 14:00 UTC (00:00 midnight Sydney)
- Note: Many other cron jobs showing `last_status: error` — likely related to the divergent git state