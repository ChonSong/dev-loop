---
name: automator
description: Automator — background task agent. Runs recurring tasks, cron jobs, and automated workflows.
version: 1.1.0
author: migrated-from-openclaw
category: agents
metadata:
  openclaw_id: automator
  openclaw_name: "Automator – Background Tasks"
---

# Automator – Background Tasks

Automator manages background tasks, recurring jobs, and automated workflows.

## Tools
- subagents, sessions_list, read, write

## Use case
Setting up and monitoring cron jobs, recurring automation, and background processing tasks.

## Known Automated Workflows

### Overnight Autonomy Engine (`hermes-sync/scripts/overnight_engine.py`)

Schedules: `*/20 14-20 * * *` (cron job `33ee3807d679` — every 20 min, 1am–7am AEDT)

**What it does:**
- Phase 1: Workspace health scan (agents, memory files, git status, security, infra, GitHub CI)
- Phase 2: Clone/pull tracked repos → run tests → log failures → check git status
- Phase 3: Write report to `workspace/memory/overnight-YYYY-MM-DD.md`; push state to `overnight-work-state.json`

**What it does NOT do (known limitations — 2026-05-01):**
- Does NOT revise the project plan dynamically — `project_plan` is a static hardcoded list
- Does NOT generate new ideas or adapt scope based on discoveries
- Does NOT fix bugs — "investigate_failures" only logs stack traces, doesn't write code or open PRs
- Does NOT iterate on test failures — it records them and moves on
- Is NOT truly "autonomous" in the creative sense — it's an automated testing & monitoring engine

**If you want true autonomy:** Phase 2 needs an LLM step that parses failures, proposes fixes, applies them via PR, and updates the next run's project plan based on what was discovered.

**State files:**
- `workspace/memory/overnight-work-state.json` — persists across runs (resets each new day)
- `workspace/memory/overnight-YYYY-MM-DD.md` — daily report

**Hardcoded config (update in script):**
```python
WRAP_UP_HOUR = 23        # 11pm Sydney = 14:00 UTC — stop accepting new work
PRIORITY_PROJECT = "repo-transmute"
TRACKED_REPOS = [
    "ChonSong/hermes-sync",
    "ChonSong/repo-transmute",
    "ChonSong/nanobot",
    "NousResearch/hermes-agent",
]
project_plan = [
    ("ChonSong/repo-transmute",  "repo-transmute", "Python", True),
    ("ChonSong/everything-dashboard", "everything-dashboard", "TypeScript", False),
]
```
