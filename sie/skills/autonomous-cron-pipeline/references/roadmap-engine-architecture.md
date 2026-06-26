# Roadmap Autonomy Engine — Architecture Reference

**Status**: LOST (script was in `/tmp/hermes-sync/scripts/`, wiped on container restart, never committed to git)
**Last known path**: `/tmp/hermes-sync/scripts/roadmap_engine.py` (~1,126 lines, v1.1)
**Cron job**: `6576b5f87515` (errors with `RuntimeError: Connection error`)

## Architecture (Reconstructed from Cron Session Transcripts)

### Three-Phase Loop

```
Phase 1: Research
  - Scan repos (clone/fetch 5 repos: repo-transmute, hermes-sync, hermes-agent, openclaw, everything-dashboard)
  - Collect TODO/FIXME entries via `_scan_todos()` (had dedup bug — 120 unique entries duplicated 3x)
  - Scan GitHub issues (requires PAT in `~/.netrc` — was missing)
  - Scan self-improvement signals (script was deleted May 8)
  - LLM planner subagent revises roadmap.json
  → Output: learnings + ideas added to roadmap.json

Phase 2: Execute
  - Select highest-priority pending tasks from roadmap.json
  - Run tests via `_execute_test()` (had bug: returned "done" instead of "blocked" when no test framework found)
  - Fix bugs, scaffold test frameworks, commit
  → Output: task status updated in roadmap.json

Phase 3: Report
  - Generate narrative report from roadmap state
  - Save to `workspace/plans/nightly-reports/report-YYYY-MM-DD.md`
  - Metrics: disk usage, memory, Docker status, GitHub CI status
  → Output: Phase 3 narrative report
```

### Key Files (All Lost)

| File | Path (last known) | Purpose |
|------|-------------------|---------|
| `roadmap_engine.py` | `/tmp/hermes-sync/scripts/` | Main engine, 3-phase loop |
| `roadmap.py` | `/tmp/hermes-sync/scripts/` | Roadmap data model |
| `reporters.py` | `/tmp/hermes-sync/scripts/` | Report generation |
| `roadmap.json` | `/opt/data/hermes-sync/workspace/plans/` | Persistent state (also gone) |
| `SKILL.md` | `/opt/data/skills/autonomous-ai-agents/roadmap-engine/` | Skill definition (also gone) |

### Known Bugs (as of May 28 v1.1)

1. `_execute_test()` returned "done" instead of "blocked" when no test framework found — **FIXED** in v1.1
2. Learnings dedup broken — 1127 entries, only 6 unique — **FIXED** in v1.1 (dedup applied)
3. Ideas dedup broken — 20+ entries, only 1 unique — **NOT FIXED**
4. Duration = 0.0h (timezone mismatch UTC/AEDT) — **NOT FIXED**
5. `git pull` fails on read-only filesystem — **WORKAROUND**: use local state
6. No GitHub PAT — CI signal scanning dead — **NOT FIXED**

### Test Framework Detection (v1.1 fix)

The v1.1 fix added `_detect_test_framework(local)` which checks:
- `pyproject.toml`, `pytest.ini`, `setup.cfg` (Python)
- `package.json` in root + `frontend/`/`client/`/`web/` subdirs (JS/TS)
- `go.mod` (Go)
- Returns `(type, workdir, extra_env)` tuple
- `extra_env` handles `PYTHONPATH=src` for repo-transmute

### Rebuild Decision Factors

**Arguments for rebuilding:**
- The engine was doing genuinely useful autonomous work
- The 3-phase pattern (research → execute → report) is sound
- The roadmap.json state model is a good design
- Multiple sessions invested in fixing bugs

**Arguments against:**
- The script was never committed — suggests the workflow wasn't mature enough
- The cron job's `deliver: local` means output goes nowhere visible
- Dependency on `/tmp/` was a fatal design flaw
- Would need to also rebuild the skill file and roadmap.json from scratch

**If rebuilding:**
1. Place engine scripts in `/workspace/roadmap-engine/` (persistent)
2. Place roadmap state in `/workspace/roadmap-engine/state/`
3. Use PHASE_TRACKER.json pattern from autonomous-cron-pipeline skill
4. Add proper dedup from the start
5. Commit everything to a git repo immediately
6. Register the output directory for backup by the hermes-sync cron
