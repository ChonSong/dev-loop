# Skill Library Conventions

## Target Shape

- **Class-level umbrella skills** with rich SKILL.md + `references/` dirs
- NOT a long flat list of narrow one-session-one-stub entries
- Each skill covers a **class of work**, not a single session

## Skill Structure

```
skill-name/
  SKILL.md          # Substantive body: purpose, workflow, templates, pitfalls, examples
  references/       # Session-specific detail, research excerpts, API docs, domain notes
  templates/        # Starter files meant to be copied and modified
  scripts/          # Statically re-runnable actions
```

## When to Update a Skill

Update the SKILL.md body (not just memory) when:
- User corrects style, tone, format, legibility, or verbosity
- User corrects workflow, approach, or sequence of steps
- Non-trivial technique, fix, workaround, or tool-usage pattern emerges
- A skill that was loaded turns out to be wrong, missing a step, or outdated

## Preference Order for Updates

1. **Update a currently-loaded skill** — the one that was in play
2. **Update an existing umbrella** — if no loaded skill fits but an existing class-level one does
3. **Add a support file** under an existing umbrella (references/, templates/, scripts/)
4. **Create a new class-level umbrella** — only when no existing skill covers the class

## What NOT to Capture

- Environment-dependent failures (missing binaries, path mismatches, unconfigured credentials)
- Negative claims about tools ("X tool is broken", "cannot use Y")
- Transient errors that resolved before the conversation ended
- One-off task narratives

## Memory vs Skills

- **Memory**: who the user is, current state of operations
- **Skills**: how to do this class of task for this user

## Skill Retrieval

When a skill is an empty stub:
1. `hermes skills search <topic>` — try first
2. `git clone --depth 1 <repo>` from known source repos
3. Only recreate from scratch as a **last resort**, marked as reconstructed

Known source repos:
- `deanpeters/Product-Manager-Skills` — PM skills
- `phuryn/pm-skills` — PM lifecycle skills
- `VoltAgent/awesome-agent-skills` — curated index
