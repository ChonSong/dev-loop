# AGENTS.md Template

Copy this to a repo root, fill in the sections, and the dev loop will discover it automatically when both AGENTS.md and .checkpoint.json exist.

```markdown
# AGENTS.md — [project-name]

## About
[One-line description. Status: active | maintenance | legacy | experiment]

## Architecture
- Stack: [language, framework, database, key services]
- Key directories: [what lives where]
- Service relations: [how API/solver/worker/DB connect]

## Conventions
- Tests: [pytest / vitest / playwright / go test — and how to run them]
- Lint: [ruff / eslint / golangci-lint — and how to run]
- Commits: [conventional commits? auto: prefix?]
- Safety: [anything an agent must NOT do — touching credentials, running destructive commands, etc.]

## Skills
Hermes skills to load when working on this project:
- [skill-name-1]
- [skill-name-2]

## Tasks

Ordered by priority. Each task is ONE unit of work for ONE player tick (one file, one feature, one test — not a whole phase).

### Task: [unique-task-id]
- **Description**: What to build, fix, or change
- **Success criteria**: Measurable outcomes — "all tests pass", "API responds 200 for /endpoint", "new page renders at /path without console errors", "schema migration is backward-compatible"
- **Coach checks**: Specific things the adversarial coach validates — "new endpoint has auth middleware", "front-end doesn't show 404", "migration can be rolled back"
- **Skills**: Task-specific skills (optional, overrides project defaults)

### Task: [next-task-id]
...

## Coach Configuration
- **Review scope**: git diff, test output, success criteria conformance, coach checks
- **Pass conditions**: All success criteria met + all coach checks pass
- **Fail actions** (descending severity):
  1. Coach creates a corrective commit on top
  2. Coach reverts the commit and creates a fix task
  3. Coach tags for human review (kanban_block)
```
