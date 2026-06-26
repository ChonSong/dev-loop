# AGENTS.md Standard — Doc-Driven Project Tracking

Defined 2026-06-15 for Sean's Hermes system. Each tracked repo gets an AGENTS.md at root + a `.checkpoint.json` tracking progress.

## Required Sections

| Section | Content |
|---------|---------|
| `## About` | One-line description + status: active / maintenance / legacy / experiment |
| `## Architecture` | Tech stack, key directories, what lives where |
| `## Conventions` | Testing, linting, commit format, anything an agent must know to work safely |
| `## Skills` | Hermes skills to load when working on this project (table: skill name, when to use, why) |
| `## Tasks` | Ordered backlog, each with task id, description, success criteria, coach checks, optional skills |
| `## Coach Configuration` | Review scope, pass conditions, fail actions (descending severity) |

## Task Entry Format

```markdown
### Task: unique-task-id
- **Description**: What to build/fix
- **Success criteria**: Measurable outcomes — "all tests pass", "API responds 200 for X", "new page renders at /path"
- **Coach checks**: Specific things the coach verifies — "schema migration is backward-compatible", "new endpoint has auth middleware"
- **Skills**: Task-specific skills beyond project defaults (optional)
```

## Checkpoint.json Format

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

## Master Checkpoint.json Format

```json
{
  "last_run": "ISO timestamp",
  "consecutive_on_project": 0,
  "active_project": "project-name",
  "projects": {
    "project-name": {
      "status": "active|pending|backlog",
      "priority": 1,
      "current_task": "task-id",
      "health": "tests_pass",
      "last_sha": "abc1234",
      "blocker": null,
      "last_review": null,
      "review_quality": null
    }
  }
}
```

**New fields (added 2026-06-15):**
- `last_review` — ISO timestamp of the most recent Coach review. The Coach sets this after each review cycle.
- `review_quality` — `"approved"`, `"fixed"`, or `"revert"`. The Coach sets this after each review verdict. The Player skips projects where this is `"revert"`.

## Discovery

The Player walks `/home/sc/repos/*/AGENTS.md`. Only repos with both AGENTS.md AND `.checkpoint.json` get dev loop cycles. If a repo has only one of the two files, it's incomplete — no cycles.

## Round-Robin

Max 2 consecutive ticks on any project. Read `consecutive_on_project` from master checkpoint. Reset to 0 when switching projects. Increment when staying on same project.
