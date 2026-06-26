---
name: blueprint
description: Turn a one-line objective into a step-by-step construction plan for multi-session projects. Each step has a self-contained context brief so a fresh agent can execute it cold. Includes dependency graph, parallel step detection, and review gate.
origin: ECC (adapted for Hermes)
---

# Blueprint — Construction Plan Generator

Turn a one-line objective into a step-by-step construction plan that any agent can execute cold.

## When to Activate

- Breaking a large feature into multiple phases with clear dependency order
- Planning a refactor or migration that spans multiple sessions
- Coordinating parallel workstreams across sub-agents
- User asks for a "plan", "blueprint", or "roadmap" for a complex task

**Do not use** for tasks completable in a single session, fewer than 3 tool calls, or when user says "just do it."

## 5-Phase Pipeline

### 1. Research
- Read project structure, existing plans, memory
- Identify current state, constraints, dependencies
- Check git branch status, auth, remote

### 2. Design
- Break objective into PR-sized steps (3-12 typical)
- Assign dependency edges: which steps must come first
- Identify parallel steps (no shared files/outputs)
- Assign model tier per step (strongest for design, default for implementation)
- Define rollback strategy per step

### 3. Draft
Write plan to `plans/<objective-name>.md`. Every step includes:
- **Context brief** — self-contained, no prior context needed
- **Task list** — specific files to create/modify
- **Verification commands** — how to confirm it worked
- **Exit criteria** — when the step is done

### 4. Review
- Adversarial review against checklist:
  - Completeness: are all steps covered?
  - Dependency correctness: is the order right?
  - Anti-patterns: any risky approaches?
  - Missing context: would a fresh agent understand?
- Fix all critical findings before finalizing

### 5. Register
- Save plan to `plans/` directory
- Present step count and parallelism summary to user
- Ready for execution

## Plan Format

```markdown
# Blueprint: [Objective Name]

**Created**: YYYY-MM-DD
**Status**: proposed | approved | in-progress | completed
**Project**: [repo name]

## Overview

[2-3 sentence description of what we're building and why]

## Dependency Graph

```
Step 1 → Step 2 → Step 4
       ↘ Step 3 ↗
```

Parallel: Steps 2 and 3 can run concurrently.

## Steps

### Step 1: [Name]
**Status**: pending
**Dependencies**: none
**Estimated**: 30 min

**Context**: [self-contained description]

**Tasks**:
- [ ] Create file `path/to/file.ts`
- [ ] Update `path/to/config.json`

**Verification**:
```bash
npm run build
npm test
```

**Exit criteria**: Build passes, tests green, no type errors

### Step 2: [Name]
**Status**: pending
**Dependencies**: Step 1
**Estimated**: 1 hour
...
```

## Parallel Step Detection

Steps can run in parallel when they:
- Don't modify the same files
- Don't depend on each other's outputs
- Don't share database migrations
- Don't have ordering dependencies

Example:
```
Step 1: Define interface (blocks everything)
Step 2A: Implement Provider A (parallel with 2B)
Step 2B: Implement Provider B (parallel with 2A)
Step 3: Integration tests (needs 2A + 2B)
```

## Q&A Design Walk (Pre-Build Alignment)

Before drafting any plan, walk the design tree with the user via sequential questions. Each answer resolves exactly one dependency for the next question. This prevents building the wrong thing and surfaces hidden assumptions early.

**Pattern:**
1. Ask the highest-leverage question that unlocks the most downstream decisions
2. Present your answer (with reasoning) — user confirms or overrides
3. Repeat until the design tree is fully resolved
4. Only then draft the plan

**Question strategy:**
- **Foundation questions first** — archive/preserve decisions before feature decisions
- **Blockers before details** — e.g., "which two repos exist and what's their relationship" before "what features does the combined system need"
- **One question per exchange** — resist batching; batching hides dependencies
- **When the user says "you decide"** — stop asking, make the call, implement

**Example from repo consolidation (May 2026):**
```
Q1: Archive hermes-computer-planning? → A: Migrate docs first, then archive ✓
Q2: Keep hermes-web-computer + agent-os merged or separate? → A: Separate repos (deployment cadences differ) — pending user confirmation
Q3: [not yet reached]
```

**When to abandon the walk:**
- Task is a simple one-shot with no meaningful design decisions
- User explicitly says "just do it" or "you decide"
- Three consecutive "you decide" answers — you've reached the boundary of useful questioning

## Hermes Adaptation

- Use `delegate_task` for parallel step execution
- Use `todo` tool to track step progress
- Plans stored in project's `plans/` directory
- For agent-os: plans go in `ChonSong/agent-os/plans/`
- For hermes-web-computer: plans go in project's `plans/` directory
- Commit plans to git for cross-session continuity
- Reference: `references/q-and-a-design-walk.md` for session transcripts of the pattern in use
