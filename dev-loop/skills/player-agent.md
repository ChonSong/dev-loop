# Player-Agent Reference

The Player implements tasks from the AGENTS.md backlog. See `~/.hermes/skills/player-agent/SKILL.md` for the full skill definition.

## Core Responsibilities

1. **Execute**: Pick next task from AGENTS.md, implement, test, commit
2. **Verify**: Run all tests before committing, fix regressions
3. **Push**: Push immediately after every commit (deploy timer rollbacks destroy un-pushed work)

## Key Principles

- **Investigate before implementing**: Read the codebase, understand patterns, then code
- **State intent before reading**: Say what you're looking for and why
- **Task size pre-check**: Fits in 2-5 minutes? If not, slice it
- **Codebase survey for unfamiliar code**: Map architecture before touching files
- **TDD**: RED → GREEN → REFACTOR every time
- **Pre-commit self-review**: Trace code path, verify against task criteria
- **End-of-tick capture**: One-paragraph note on what changed, learned, pending

## Workflow

```
1. Discover repos with AGENTS.md + checkpoint
2. Read project checkpoint → current_task
3. Check round-robin (max 2 consecutive per project)
4. State intent: "Reading X to understand Y"
5. Codebase survey (if unfamiliar): map the subsystem
6. Task size pre-check: fits one tick?
7. Design tree walk (if ambiguous): one decision at a time
8. TDD: RED → GREEN → REFACTOR
9. Run all tests
10. Fix regressions or revert
11. Pre-commit self-review
12. Commit
13. Push (IMMEDIATELY)
14. Verify deploy picked it up
15. End-of-tick capture
16. Update checkpoint
```

## Time Budget

| Phase | Target | Hard Limit |
|-------|--------|------------|
| State intent + codebase survey | 30s | 60s |
| Task size pre-check | 10s | 20s |
| Design tree walk | 30s | 60s |
| Implementation | 120s | 180s |
| TDD cycle | 60s | 120s |
| Pre-commit self-review | 30s | 60s |
| Test suite | 180s | 300s |
| End-of-tick capture | 15s | 30s |

Total: ~500s hard limit. Exceed it and the cron kills the job.

## Safety Valve: Task Exhaustion Recovery

The Coach is the PRIMARY backlog generator. If the Coach failed to run, the Player may add tasks when:
1. `current_task` is `"tbd"` AND
2. All completed entries have coach approval AND
3. User-facing features are still broken

Before generating, check if the Coach already handled it (look for a "chore: add user-facing tasks" commit).

## Composing with Other Skills

| Skill | When |
|-------|------|
| `software-development/writing-plans` | Task too large for one tick |
| `software-development/test-driven-development` | Every code change |
| `software-development/scrutinize` | Pre-commit self-review |
| `software-development/development-communication` | Exploration and implementation |
| `software-development/spec-audit` | Task references a spec/GDD |
| `planning/blueprint` | Ambiguous task needs direction |
| `software-development/systematic-debugging` | Tests fail unexpectedly |
