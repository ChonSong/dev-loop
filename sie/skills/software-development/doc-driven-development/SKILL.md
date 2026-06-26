---
name: doc-driven-development
description: "Autonomous development loop driven by per-repo AGENTS.md + checkpoint.json. Each repo self-describes, the player loop reads and executes, the coach loop adversarially validates. Implements dialectical autocoding (g3 coach/player pattern)."
tags: ["autonomous", "doc-driven", "adversarial", "coach-player", "project-tracking", "checkpoint"]
related_skills: ["autonomous-development", "subagent-driven-development", "writing-plans"]
---

# Doc-Driven Development

## Overview

A methodology for autonomous development where **every repo documents itself**. The player loop reads AGENTS.md to find work, executes it, and commits. The coach loop reviews every commit adversarially against success criteria defined in AGENTS.md.

Inspired by g3's dialectical autocoding (Block AI Research, Dec 2025) — a structured coach/player adversarial loop where two agents with different system prompts cooperate: player implements, coach reviews, iterate until the coach signs off. See `references/g3-research.md`.

## Core Architecture

```
┌─────────────────────────────┐
│     Repo Discovery           │
│  Walk /repos/*/AGENTS.md    │
│  + checkpoint.json          │
└──────┬──────────────────────┘
       │
┌──────▼──────────────────────┐     ┌─────────────────────────────┐
│  PLAYER (cron :00 every hr) │     │  COACH (cron :05 every hr)  │
│  - Read AGENTS.md task      │     │  - Read last commit diff    │
│  - Load declared skills     │     │  - Validate vs success crit │
│  - Implement                │     │  - Run coach checks         │
│  - Run all tests            │     │  - APPROVE / FIX / REVERT   │
│  - Commit                   │     │  - Update checkpoint        │
│  - Update checkpoint        │     └──────────┬──────────────────┘
└──────┬──────────────────────┘                │
       │                                       │
       └─────────── master-checkpoint.json ────┘
```

**Key idea**: Coach and player use different models. Player runs on a fast/cheap model for throughput. Coach runs on a stronger model for thorough review. They run as separate cron jobs offset by 5 minutes.

## When to Use

- Setting up autonomous development for a project
- Adding a new repo to the autonomous loop
- Designing the tracking/checkpoint system for a monorepo
- Debugging why the dev loop isn't making progress on a project
- Any time you need a project to make progress without human intervention

**Do NOT use for**: One-off tasks (use `delegate_task`), visual QA work (use `autonomous-development` skill), multi-agent orchestration with different profiles (use `kanban-orchestrator`).

## Setup Procedure

### 1. Create AGENTS.md

Every tracked repo gets an AGENTS.md at the root with:

- **About**: project description, current status (active/maintenance/legacy)
- **Architecture**: stack, key directories, service relationships
- **Conventions**: testing requirements, linting, commit format
- **Skills**: Hermes skills to load when working on this project
- **Tasks**: ordered backlog, each with:
  - Unique task ID
  - Description
  - **Success criteria** — measurable outcomes ("all tests pass", "API returns 200", "page renders without errors")
  - **Coach checks** — specific things the coach verifies (schema backward-compatibility, auth middleware present, no console errors)
  - Task-specific skills (optional)
- **Coach Configuration**: review scope, pass conditions, fail actions (patch > revert > human-review)

See `references/AGENTS.md-template.md` for the canonical template.

### 2. Create checkpoint.json

```json
{
  "project": "project-name",
  "repo": "/home/sc/repos/project-name",
  "current_task": "task-id-from-agents-md",
  "completed": [
    {"task": "task-id", "sha": "abc1234", "date": "2026-06-15", "coach": "approved"}
  ],
  "health": "tests_pass|tests_fail|unknown",
  "last_sha": "abc1234",
  "blocker": null
}
```

See `references/checkpoint-standard.md` for the full spec.

### 3. Set up Master Checkpoint

The master checkpoint at `/home/sc/.hermes/master-checkpoint.json` tracks active projects, their priority, and the round-robin counter:

```json
{
  "last_run": "ISO_TIMESTAMP",
  "consecutive_on_project": 1,
  "active_project": "current-project",
  "projects": {
    "project-a": {"status": "active", "priority": 1, "current_task": "...", "health": "...", "last_sha": "...", "blocker": null},
    "project-b": {"status": "active", "priority": 2, ...}
  }
}
```

### 4. Create Player Cron

Cron at `0 * * * *`, loads `player-agent` skill, plus AGENTS.md project skills:

```yaml
# cron job config
schedule: "0 * * * *"
skills: ["player-agent"]
```

The `player-agent` skill defines the role. The cron prompt defines the per-tick mechanics:

1. SSH to host, walk `/home/sc/repos/*/AGENTS.md` for repos with both AGENTS.md + checkpoint.json
2. Read master checkpoint — if `consecutive_on_project >= 2`, skip to next repo
3. Read chosen repo's AGENTS.md + checkpoint to find next pending task
4. Load project skills declared in AGENTS.md `## Skills` section
5. Execute: implement, run ALL tests (not just new ones), fix failures
6. Commit with conventional commit message
7. Update both checkpoint + master checkpoint
8. Report: `✅ [project] player: [task]. SHA: [sha]. Tests: [result]. Next: [next task]`

### 5. Create Coach Cron

Cron at `5 * * * *`, loads `coach-agent` skill:

```yaml
# cron job config
schedule: "5 * * * *"
skills: ["coach-agent"]
```

Per-tick flow:

1. Read master checkpoint to find most recent player completion
2. Read AGENTS.md success criteria + coach checks for that task
3. Read git diff + test output
4. Validate each criterion independently with **evidence** (curl endpoints, run tests, quote diffs)
5. Decide:
   - **APPROVE**: all pass → update checkpoint with `coach: "approved"`
   - **FIX**: minor issues → create corrective commit → update as approved
   - **FAIL**: critical issues → revert player's commit → restore previous current_task
6. If no new player commits to review since last coach run, report `[SILENT]`
7. Report: `✅ [project] coach: approved` or `❌ [project] coach: reverted — [reason]`

## Coach Review Discipline

The coach is an **adversarial agent**, not a rubber stamp:

- Challenge assumptions, don't nitpick style
- Prefer fixing over reverting when the fix is obvious and bounded
- Test output is the strongest signal — never override failing tests
- For ambiguous issues, write a detailed review and approve with caveats
- If tests didn't run (broken env), note it but don't block — that's a separate task

### Per-Task Coach Checks

Each task in AGENTS.md declares specific coach checks — concrete things the coach verifies beyond just "tests pass":
- "Schema migration is backward-compatible" — coach checks for ALTER TABLE DROP COLUMN, etc.
- "New endpoint has auth middleware" — coach inspects route decorators
- "Frontend page loads without console errors" — coach runs a headless browser check
- "API returns 200 for all known variant IDs" — coach curls each variant
- "No unrelated files changed" — coach checks git diff scope

These checks are what differentiate a rubber-stamp from an adversarial review. Each check must be independently verifiable with a command or code inspection.

Fail actions in descending severity:
1. Coach creates a corrective commit fixing the issue directly
2. Coach reverts the player's commit and restores the previous checkpoint state
3. For ambiguous or high-risk failures, coach blocks and tags for human review

## Skills Integration

Three layers of skills get loaded when the player works on a project:

| Layer | Where | Loaded by | Example |
|-------|-------|-----------|---------|
| **Role** | player-agent/coach-agent skills | Cron job `skills:` config | `player-agent`, `coach-agent` |
| **Project** | AGENTS.md `## Skills` table | Player reads and loads | `subagent-driven-development`, `test-driven-development` |
| **Task** | Per-task `Skills:` in backlog | Player loads for that tick only | `systematic-debugging` (when tests fail) |

The role skill (player-agent) is always loaded. The project skills are loaded when that project is selected. Task skills override/extend for specific tasks.

## Ongoing Assessment

Built into the daily memory curation cron (16:00 daily). Each run:
1. Walks all tracked projects (those with AGENTS.md + checkpoint.json)
2. Reads each checkpoint — current_task, completed count, last SHA
3. Reads git log since last checkpoint SHA — counts commits by agent type (player vs coach)
4. Flags stalled tasks — current_task unchanged for >48h
5. Evaluates coach quality — what proportion of reviews were APPROVE vs FIX vs REVERT
6. Writes audit to `/home/sc/.hermes/memory/curation-logs/YYYY-MM-DD.md`

## Common Pitfalls

1. **Rushing to implementation before investigation**. When asked to design a system, do NOT jump to code. First: investigate existing approaches (g3's dialectical autocoding, alternatives), explore codebases, read specs, ask clarifying questions, present options before building. The user explicitly called this out: "investigate ask questions and explore codebases where required." If the model you're running on isn't capable of architectural design (e.g., flash models), Acknowledge the limitation and defer design decisions to a stronger model rather than producing a shallow implementation. See also `search-first` skill for the research-before-building workflow.

2. **Hardcoding projects in the loop prompt instead of discovering them** — leads to stale entries and no way to add new repos without editing the cron job. Always discover via AGENTS.md glob.

3. **No success criteria** — the loop keeps adding phases to the same project (the "energy router problem"). Every task must have measurable success criteria so the coach knows when it's done.

4. **Coach on the same model as player** — defeats the purpose of adversarial review. Coach should use a stronger model capable of deeper analysis.

5. **Skipping test runs** — the player must run ALL existing tests, not just new ones. Regression detection is the whole point of testing.

6. **Checkpoint getting out of sync with git HEAD** — happens when commits happen outside the loop (manual work, other cron jobs). Always read `git log -1 --oneline` and checkpoint's `last_sha` and reconcile if they diverge.

7. **Dead projects in master checkpoint** — projects with "repo not found" blockers waste ticks. Remove them from the master checkpoint when they become unreachable.

8. **Self-review is not adversarial** — a single agent reviewing its own work in the same session is a rubber stamp. The coach must be a separate session with a fresh perspective (hence a separate cron job). If the same model runs both roles, the coach needs a different system prompt that forces it to be critical, not compliant.

## Related Skills

- `autonomous-development` — visual QA / CSS iteration pipeline (different domain, complementary)
- `kanban-orchestrator` — multi-agent profile-based task routing (for when you need human-in-the-loop)
- `writing-plans` — writing implementation plans with task decomposition
- `subagent-driven-development` — parallel subagent delegation for complex features

## References

- `references/g3-research.md` — dialectical autocoding pattern from block/dhanji g3
- `references/AGENTS.md-template.md` — canonical AGENTS.md template with annotations
- `references/checkpoint-standard.md` — full checkpoint.json format specification

## Design Document

The full design for this system lives at `design/dev-loop-v2.md` in the workspace.
