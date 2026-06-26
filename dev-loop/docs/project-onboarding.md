# Project Onboarding

Add a new project to the dev loop in 5 steps.

## Step 1: Investigate the Codebase

Before writing AGENTS.md, understand the project:
- Architecture, stack, key directories
- Test framework and whether tests actually run
- Current git log (recent commits, conventions)
- What end-user value the project delivers

## Step 2: Write AGENTS.md

Copy `templates/AGENTS.md` to the repo root. Fill in:

```markdown
# AGENTS.md — Project Name

## About
One-line description. Status: active | maintenance | legacy | experiment

## Architecture
- Stack (language, framework, database)
- Key directories and their roles
- Service relations (API → solver → DB)

## Conventions
- Testing: how to run the test suite
- Linting: how to run lint
- Commits: conventional commits
- Safety: what agents must never do

## Skills
Hermes skills to load for this project:
- skill-name-1
- skill-name-2

## Tasks

### Task: first-task
- **Description**: One sentence, specific
- **Success criteria**: Measurable — "tests pass", "API returns 200"
- **Coach checks**: Verifiable — "auth enforced", "migration backward-compatible"
```

### Task Design Principles

**Success criteria** must be:
- Measurable: "Tests pass", "API returns 200", "Page renders without errors"
- Verifiable: The Coach can check each independently
- Bounded: Achievable in one player tick (2-5 minutes)
- Not vague: Avoid "Improve quality" or "Polish UI"

**Coach checks** should be:
- Security-aware: "Auth is enforced", "Input is validated"
- Regression-aware: "Existing tests still pass", "Schema backward-compatible"
- Evidence-based: Can be checked with curl, test runs, or diff inspection

## Step 3: Write .checkpoint.json

Copy `templates/checkpoint.json` to the repo root:

```json
{
  "project": "project-name",
  "repo": "/home/sc/repos/project-name",
  "current_task": "first-task-id",
  "completed": [],
  "health": "unknown",
  "last_sha": "",
  "blocker": null
}
```

## Step 4: Register in Master Checkpoint

Copy `templates/master-checkpoint.json` to `~/.hermes/master-checkpoint.json`:

```json
{
  "last_run": "2026-06-16T00:00:00Z",
  "consecutive_on_project": 0,
  "active_project": "project-name",
  "projects": {
    "project-name": {
      "status": "active",
      "priority": 1,
      "current_task": "first-task-id",
      "health": "unknown",
      "last_sha": "",
      "blocker": null,
      "last_review": null,
      "review_quality": null
    }
  }
}
```

## Step 5: Cron Jobs Handle the Rest

The Player cron (every hour at :00) discovers the new AGENTS.md + checkpoint, reads the first task, and starts implementing. The Coach (at :05) reviews.

### Notes

- Only repos with BOTH AGENTS.md and .checkpoint.json get cycles
- Priority 1 = highest. Projects with the same priority rotate round-robin
- Max 2 consecutive ticks on any project
- Dead entries (projects where "repo not found") should be removed from the master checkpoint
