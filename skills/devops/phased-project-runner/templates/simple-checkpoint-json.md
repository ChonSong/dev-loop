# Simple Checkpoint Template (single-file variant)

An alternative to `STATE_DIR/CHECKPOINTS/phase-N-*.json` for simpler projects.
Single `.checkpoint.json` at the repo root — easy to read, write, and parse.

## Template

```json
{
  "project": "energy-aware-task-router",
  "repo": "/home/sc/repos/energy-aware-task-router",
  "phase": 1,
  "phase_name": "Project Foundation",
  "completed": [],
  "current": null,
  "next": "Add .gitignore + project restructure",
  "health": "no_tests_yet",
  "last_sha": null
}
```

## Fields

| Field | Purpose |
|---|---|
| `project` | Human-readable project name |
| `repo` | Absolute path to the repo on disk |
| `phase` | Current phase number (1-N) |
| `phase_name` | Human-readable phase name |
| `completed` | Array of completed task descriptions |
| `current` | Current in-progress task (null if idle) |
| `next` | Next task to execute |
| `health` | Test status: `no_tests_yet`, `tests_pass`, `tests_failing:N` |
| `last_sha` | Git SHA of last commit (null if no commits) |

## Update Pattern (each cron run)

```
1. Read checkpoint: cat .checkpoint.json
2. Execute next task
3. Run tests
4. If pass:
   - git add -A && git commit
   - Update checkpoint: append to completed, set next, update last_sha
   - Write: cat > .checkpoint.json << 'EOF'
5. If fail:
   - Fix, or set health to "tests_failing:N" and stop
```

## When to use this vs phased-project-runner's STATE_DIR approach

**Use single-file checkpoint when:**
- One-person project (no team coordination needed)
- Simple linear phase progression (no branching/parallel phases)
- Cron-driven development (one task per run)
- No need for phase-specific failure history

**Use STATE_DIR/CHECKPOINTS/ when:**
- Multiple agents/people working on different phases
- Need historical phase-by-phase failure records
- Complex phase dependencies or retry logic per phase
- Resume interrupted phases with exact state recovery
