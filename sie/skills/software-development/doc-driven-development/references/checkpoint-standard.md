# Checkpoint.json Standard

Per-repo progress tracker. Mirrors the AGENTS.md task backlog.

## Schema

```json
{
  "project": "project-name",
  "repo": "/absolute/path/to/repo",
  "current_task": "task-id-from-agents-md",
  "completed": [
    {
      "task": "task-id",
      "sha": "abc1234",
      "date": "2026-06-15",
      "coach": "approved"
    }
  ],
  "health": "tests_pass | tests_fail | tests_unknown",
  "last_sha": "abc1234",
  "blocker": "description of why blocked | null"
}
```

## Field Rules

| Field | Required | Description |
|-------|----------|-------------|
| `project` | Yes | Matches AGENTS.md project name |
| `repo` | Yes | Absolute path to git repo |
| `current_task` | Yes | Must match a task ID in AGENTS.md `## Tasks` |
| `completed[]` | Yes | Array of completed tasks |
| `completed[].task` | Yes | Task ID from AGENTS.md |
| `completed[].sha` | Yes | Git commit SHA when completed |
| `completed[].date` | Yes | ISO date of completion |
| `completed[].coach` | No | "approved" or "failed" after coach review; null/absent before review |
| `health` | Yes | Current test status |
| `last_sha` | Yes | HEAD commit SHA of the repo |
| `blocker` | No | Non-null string if the project is blocked; null/absent if unblocked |

## Lifecycle

1. Player reads checkpoint → finds `current_task`
2. Player reads AGENTS.md → finds that task's description, success criteria, coach checks
3. Player implements → tests → commits → updates `completed[]` + `current_task` + `last_sha`
4. Coach reads checkpoint → finds last completed task (where `coach` is missing/null)
5. Coach reviews → sets `coach: "approved"` or `coach: "failed"` on that entry
6. If coach reverts → removes the completed entry, restores previous `current_task`

## Master Checkpoint

Central tracking at `/home/sc/.hermes/master-checkpoint.json`:

```json
{
  "last_run": "2026-06-15T10:00:00Z",
  "consecutive_on_project": 1,
  "active_project": "gto-wizard-clone",
  "projects": {
    "project-a": {
      "status": "active",
      "priority": 1,
      "current_task": "task-id",
      "health": "tests_pass",
      "last_sha": "abc1234",
      "blocker": null
    }
  }
}
```

The master checkpoint drives round-robin scheduling: `consecutive_on_project >= 2` triggers a switch to the next priority project.
