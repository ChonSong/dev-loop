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
- Commits: [conventional commits]
- Safety: [anything an agent must NOT do]

## Skills
Hermes skills to load when working on this project:
- [skill-name-1]
- [skill-name-2]

## Tasks

Ordered by priority. Each task is ONE unit of work for ONE player tick.

### Task: [unique-task-id]
- **Description**: What to build, fix, or change — one sentence, specific
- **Success criteria**: Measurable outcomes — "all tests pass", "API responds 200 for /endpoint", "new page renders at /path without console errors"
- **Coach checks**: Specific things the coach verifies — "new endpoint has auth middleware", "frontend doesn't show 404", "migration can be rolled back"

### Task: [next-task-id]
- ...

## Coach Configuration
- **Review scope**: git diff, test output, success criteria conformance, coach checks
- **Pass conditions**: All success criteria met + all coach checks pass
- **Fail actions** (descending severity):
  1. Coach creates a corrective commit on top
  2. Coach reverts the commit and creates a fix task
  3. Coach tags for human review
