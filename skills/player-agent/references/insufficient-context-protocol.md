# Insufficient Context — Research Protocol

From g3 research (June 15): how g3 handles tasks where context is thin.

## The Problem

When a task's success criteria don't clearly map to specific code changes, agents either:
- **Guess and implement** — wastes cycles, often wrong, user frustration
- **Ask the user** — breaks autonomy, user doesn't want to hand-hold

## g3's Approach: Plan Discipline

g3 uses `plan_write` which **forces** context gathering before any implementation:

Each plan item MUST have:
- `touches`: Exact file paths the change affects (forces agent to find them first)
- `checks`: Three perspectives — `happy` (normal success), `negative` (error handling), `boundary` (edge cases)
- `evidence` (required when done): File:line refs, test names

This means an agent cannot start coding until it can name the files it will touch and what success looks like. The act of specifying `touches` forces codebase exploration.

## Applying to Our System

When the player encounters a task with thin context:

1. **Name the files first**: Before writing code, use `rg`/code_search to find the relevant files. State: "This task touches [file A], [file B], [file C]."
2. **Define checks per file**: For each file, what's the happy path? What errors could occur? What edge cases exist?
3. **Only then implement**: Code comes after context gathering, not before.

When context is so thin you can't even name the files (unfamiliar library, new domain):

1. **Web search**: Search for the library/API/pattern. Read docs or examples.
2. **Codebase search**: Find how other parts of the project use similar patterns.
3. **State assumptions**: "I assume this pattern follows [X] based on [evidence]. Proceeding."

## Scout Agent Pattern (g3)

For bounded research tasks, g3 has a dedicated Scout agent (`agents/scout.md`) that:
- Takes a specific research question
- Returns a one-page brief with options, tradeoffs, and recommendation
- Does NOT explore endlessly, brainstorm, or teach
- Does NOT write code or modify files

When player context is thin enough that a codebase search isn't enough, this is the right pattern: scope a specific research question, do bounded research, produce a decision-ready brief, then implement.

## Summary

| Context Level | Action | Evidence |
|--------------|--------|----------|
| Files are known | Name touches, define checks, implement | File paths, test names |
| Files unknown, domain known | Codebase search, find patterns | grep/rg results, similar file patterns |
| Domain unknown | Web search + Scout-style brief | Docs, examples, tradeoff notes |
| Still ambiguous | Document assumptions, proceed | Assumption note in commit message |
