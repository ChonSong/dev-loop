# AGENTS.md Template

```markdown
# AGENTS.md — [project-name]

## About
One-line description. Current status: active | maintenance | legacy | experiment

## Architecture
- Stack (language, framework, database, key libraries)
- Key directories and what they contain
- How services relate (e.g., API → solver → DB)

## Conventions
- Testing requirements (framework, how to run)
- Linting/code style (tool + config location)
- Commit message format
- Branch strategy
- Any agent-specific gotchas

## Skills
Hermes skills to load when working on this project:

| Skill | When | Why |
|-------|------|-----|
| `skill-name` | Condition | Rationale |

## Tasks

Ordered by priority. Each task is ONE unit of work (one player tick).

### Task: unique-task-id
- **Description**: What to build or fix in 1-2 sentences.
- **Success criteria**: Measurable, verifiable outcomes. NOT "works correctly." DO say "all 27 tests pass with exit 0," "API returns 200 for all variant IDs," "page renders without console errors," "frontend build completes without warnings."
- **Coach checks**: Specific things the coach verifies independently. NOT "code looks good." DO say "schema migration is backward-compatible (no DROP COLUMN)," "new endpoint has auth middleware," "no unrelated files changed in the diff."
- **Skills**: Task-specific skills (optional — overrides project defaults for this task).

### Task: next-task-id
...

## Coach Configuration
- **Review scope**: git diff of last commit, test output, success criteria conformance, coach checks
- **Pass conditions**: all success criteria met AND all coach checks pass
- **Fail actions** (descending severity):
  1. Coach creates a corrective commit fixing the issue directly
  2. Coach reverts the player's commit and restores previous checkpoint state
  3. Coach blocks and tags for human review (ambiguous or high-risk failures)
```
