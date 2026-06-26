# Task Ownership Architecture — Coach Generates, Player Executes

## Why This Matters

The dev loop's most persistent failure mode was **self-referential task generation**. The Player generated its own tasks via Task Exhaustion Recovery — but those tasks were based on what the Player already knew about the codebase, not what was actually broken from an external reference.

The Coach has the browser, sees the original app, and identifies real bugs. Only the Coach can generate **externally-validated tasks**.

## The Broken Pattern (Before 2026-06-25)

```
Player: "I've finished all tasks in AGENTS.md. I'll write new tasks for myself."
  → tasks describe fixing code the Player already wrote
  → tests validate the Player's implementation decisions
  → Coach reviews but only adds spec_gaps, never replenishes AGENTS.md
  → Loop stalls when backlog empties
Culmination: current_task: "tbd", project has no active task, Coach flags stagnation but can't unstick it
```

## The Fix (2026-06-25)

```
Coach Step 4: After every review with findings, write 2-5 AGENTS.md tasks
  → tasks are based on browser-verified evidence against the original
  → tasks describe user-visible behavior, not code changes
  → Player picks the first unstarted task, executes, commits
  → Coach reviews next cycle with the new evidence
```

## Task Format (from Coach Step 4)

```
### Task: fix-{short-description}

**Description:** What needs to happen, referencing the evidence you found.

**Success criteria:** What the fix requires in terms of user-visible behavior, not code changes.

**Coach checks:** What you will verify on the live page next cycle.
```

## Concrete Example from 2026-06-25

**Evidence found during browser QA:**
- Polytopia tribe selection: clicking Bardur starts Xin-xi
- Root cause: `SelectScene` sorts tribes alphabetically for display but passes the sorted index as `humanTraitIndex`, while `GameScene` indexes into the unsorted `TRIBE_CONFIGS`

**Generated task:**

```
### Task: fix-tribe-selection-sort-mismatch

**Description:** SelectScene sorts tribes alphabetically for display but passes the sorted index as humanTraitIndex to GameScene, which indexes into the unsorted TRIBE_CONFIGS array. Every tribe card click starts the wrong game — clicking Bardur starts Xin-xi, etc.

**Success criteria:** Clicking each tribe card starts the correct tribe's game, not an alphabetically-adjacent one.

**Coach checks:** Click each tribe card, verify the correct tribe name appears on the next scene.
```

## What the Player Should NOT Do

- **Do NOT generate tasks for yourself** — that's the old self-referential pattern. If AGENTS.md is empty, wait for the next Coach cycle (max 30min) or trigger Task Exhaustion Recovery ONLY if Coach hasn't reviewed in 6+ hours.
- **Do NOT write "Add E2E test for X" tasks** — these are methodology failures by definition (test validates implementation, not requirement). The pre-commit hook blocks them anyway.
- **Do NOT skip the Coach's task priority order** — AGENTS.md order IS the priority. P1 bugs first, then P2 gaps, then visual match.

## How to Detect Task Ownership Failure

| Signal | Diagnosis |
|--------|-----------|
| Player's Task Exhaustion Recovery fires regularly | Coach isn't generating enough tasks — check Coach output for Step 4 execution |
| AGENTS.md has self-referential tasks ("Add E2E test for X") | Player's Task Exhaustion Recovery ran — these should be rewritten by Coach |
| current_task: "tbd" + no active tasks | Coach cycled but didn't execute Step 4 — Coach skill might be too long, or model isn't following instructions |
| Same bug stagnant for 3+ cycles | Coach found it (added spec_gap) but didn't generate a task for it — Step 4 execution gap |
