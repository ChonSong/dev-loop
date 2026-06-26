---
name: roadmap-engine
description: "Roadmap Autonomy Engine — long-horizon autonomous planning and execution system. Runs Phase 1 research / Phase 2 execute / Phase 3 narrative report. Rebuilt from scratch June 2026 after the original scripts were lost."
tags: [autonomous, planning, pipeline, roadmap, self-improvement]
---

# roadmap-engine

Roadmap Autonomy Engine — long-horizon autonomous planning and execution system. Runs Phase 1 research → Phase 2 execute → Phase 3 narrative report.

## Recovery from Scratch (June 2026)

The entire /opt/data/hermes-sync repo was deleted. Rebuilt from skill architecture docs in one session:
- All 6 scripts recreated at /tmp/hermes-sync/scripts/
- Seed roadmap.json with current projects/tasks
- Scripts are now simpler — executor/planner/research modules inlined into roadmap_engine.py

Prevent re-loss: /tmp/hermes-sync/ is ephemeral. Git-init and push to a backup repo.

## Architecture

```
Phase 1 RESEARCH:
  Load roadmap.json → git-sync repos → scan TODOs/FIXMEs
  → self-improvement scan → save snapshot

Phase 2 EXECUTE:
  Load top tasks from roadmap → verify preconditions → execute
  → record results → update roadmap

Phase 3 REPORT:
  Generate narrative report → save to nightly-reports/ → stdout
```

## Usage

cd /tmp/hermes-sync && python3 scripts/roadmap_engine.py --phase all
python3 scripts/roadmap_engine.py --phase research|execute|report

## Scripts

All at /tmp/hermes-sync/scripts/:
- roadmap.py (~400 lines) — Data model + CRUD + scoring formula
- roadmap_engine.py (~540 lines) — Phase 1/2/3 pipeline with inline executors
- reporters.py (~300 lines) — Narrative markdown report generator
- self_improvement.py (~120 lines) — Orchestrator: scan → author pipeline
- learnings_scanner.py (~380 lines) — 4-source scan + score + rank
- skill_author.py (~325 lines) — DRY-RUN SKILL.md authoring

## Common Pitfalls

1. Scripts on /tmp are ephemeral — lost on container restart. Git-init + push after any changes.
2. No external dependencies — scripts use stdlib only.
3. Phase 2 executors are simplified — inline in roadmap_engine.py.
4. If disk >92% — don't declare it a blocker. Flag usage + offer options.
5. The old separate-module architecture (executor.py, planner.py, research.py) was inlined — don't recreate them.

## Verification

- cd /tmp/hermes-sync && python3 scripts/roadmap_engine.py --phase all runs <15s
- Report appears in workspace/plans/nightly-reports/
- python3 scripts/self_improvement.py --scan-only finds candidates
