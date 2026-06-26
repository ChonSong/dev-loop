---
name: subagent-driven-development
description: "Execute plans via delegate_task subagents (2-stage review)."
version: 1.1.0
author: Hermes Agent (adapted from obra/superpowers)
license: MIT
metadata:
  hermes:
    tags: [delegation, subagent, implementation, workflow, parallel]
    related_skills: [writing-plans, requesting-code-review, test-driven-development]
---

# Subagent-Driven Development

## Overview

Execute implementation plans by dispatching fresh subagents per task with systematic two-stage review.

**Core principle:** Fresh subagent per task + two-stage review (spec then quality) = high quality, fast iteration.

## When to Use

Use this skill when:
- You have an implementation plan (from writing-plans skill or user requirements)
- Tasks are mostly independent
- Quality and spec compliance are important
- You want automated review between tasks

**vs. manual execution:**
- Fresh context per task (no confusion from accumulated state)
- Automated review process catches issues early
- Consistent quality checks across all tasks
- Subagents can ask questions before starting work

## The Process

### 1. Read and Parse Plan

Read the plan file. Extract ALL tasks with their full text and context upfront. Create a todo list:

```python
# Read the plan
read_file("docs/plans/feature-plan.md")

# Create todo list with all tasks
todo([
    {"id": "task-1", "content": "Create User model with email field", "status": "pending"},
    {"id": "task-2", "content": "Add password hashing utility", "status": "pending"},
    {"id": "task-3", "content": "Create login endpoint", "status": "pending"},
])
```

**Key:** Read the plan ONCE. Extract everything. Don't make subagents read the plan file — provide the full task text directly in context.

### 2. Per-Task Workflow

For EACH task in the plan:

#### Step 1: Dispatch Implementer Subagent

Use `delegate_task` with complete context:

```python
delegate_task(
    goal="Implement Task 1: Create User model with email and password_hash fields",
    context="""
    TASK FROM PLAN:
    - Create: src/models/user.py
    - Add User class with email (str) and password_hash (str) fields
    - Use bcrypt for password hashing
    - Include __repr__ for debugging

    FOLLOW TDD:
    1. Write failing test in tests/models/test_user.py
    2. Run: pytest tests/models/test_user.py -v (verify FAIL)
    3. Write minimal implementation
    4. Run: pytest tests/models/test_user.py -v (verify PASS)
    5. Run: pytest tests/ -q (verify no regressions)
    6. Commit: git add -A && git commit -m "feat: add User model with password hashing"

    PROJECT CONTEXT:
    - Python 3.11, Flask app in src/app.py
    - Existing models in src/models/
    - Tests use pytest, run from project root
    - bcrypt already in requirements.txt
    """,
    toolsets=['terminal', 'file']
)
```

#### Step 2: Dispatch Spec Compliance Reviewer

After the implementer completes, verify against the original spec:

```python
delegate_task(
    goal="Review if implementation matches the spec from the plan",
    context="""
    ORIGINAL TASK SPEC:
    - Create src/models/user.py with User class
    - Fields: email (str), password_hash (str)
    - Use bcrypt for password hashing
    - Include __repr__

    CHECK:
    - [ ] All requirements from spec implemented?
    - [ ] File paths match spec?
    - [ ] Function signatures match spec?
    - [ ] Behavior matches expected?
    - [ ] Nothing extra added (no scope creep)?

    OUTPUT: PASS or list of specific spec gaps to fix.
    """,
    toolsets=['file']
)
```

**If spec issues found:** Fix gaps, then re-run spec review. Continue only when spec-compliant.

#### Step 3: Dispatch Code Quality Reviewer

After spec compliance passes:

```python
delegate_task(
    goal="Review code quality for Task 1 implementation",
    context="""
    FILES TO REVIEW:
    - src/models/user.py
    - tests/models/test_user.py

    CHECK:
    - [ ] Follows project conventions and style?
    - [ ] Proper error handling?
    - [ ] Clear variable/function names?
    - [ ] Adequate test coverage?
    - [ ] No obvious bugs or missed edge cases?
    - [ ] No security issues?

    OUTPUT FORMAT:
    - Critical Issues: [must fix before proceeding]
    - Important Issues: [should fix]
    - Minor Issues: [optional]
    - Verdict: APPROVED or REQUEST_CHANGES
    """,
    toolsets=['file']
)
```

**If quality issues found:** Fix issues, re-review. Continue only when approved.

#### Step 4: Mark Complete

```python
todo([{"id": "task-1", "content": "Create User model with email field", "status": "completed"}], merge=True)
```

### 3. Final Review

After ALL tasks are complete, dispatch a final integration reviewer:

```python
delegate_task(
    goal="Review the entire implementation for consistency and integration issues",
    context="""
    All tasks from the plan are complete. Review the full implementation:
    - Do all components work together?
    - Any inconsistencies between tasks?
    - All tests passing?
    - Ready for merge?
    """,
    toolsets=['terminal', 'file']
)
```

### 4. Verify and Commit

```bash
# Run full test suite
pytest tests/ -q

# Review all changes
git diff --stat

# Final commit if needed
git add -A && git commit -m "feat: complete [feature name] implementation"
```

## Parallel Track Mode (for large codebases)

**When the serial task-by-task pattern is too slow**, use parallel track delegation:

1. Write a detailed `PLAN.md` with every interface, file path, and data flow locked
2. Define 3-6 tracks, each owning **non-overlapping file sets**
3. Dispatch all tracks simultaneously via `delegate_task`
4. Each subagent writes files and pushes commits independently
5. After all tracks complete, verify build + vet pass

**Critical rules:**
- Each track MUST have exclusive file ownership. If two tracks touch the same file, they'll conflict.
- The PLAN.md must specify exact file paths for every track.
- Include a final integration track (Track N) that wires all packages together.
- Each track should push commits frequently — one subagent may fail while others succeed.

### API/Interface Alignment (Cross-Track Contract)

**This is the #1 cause of parallel mode failures.** When tracks share a common type system (HexCoord, Tile, Unit, City, etc.), each subagent independently decides the API surface. After merge, you get mismatches: one track exports `makeDecisions(tribe, state)`, another expects `decide(state, phase)`.

**Before dispatching parallel tracks, LOCK THE SHARED INTERFACES:**

1. In the context for EVERY track, include exact type definitions for all shared types:
   ```
   // ALL tracks MUST use these exact signatures:
   // Unit: constructor(public position: HexCoord, public type: UnitType, public owner: string, health = 10)
   // Unit.getAliveUnits(): Unit[]
   // City: constructor(position: HexCoord, name: string, tribeId: string, level = 1, population = 1)
   // Tribe: constructor(config: TribeConfig)  // TribeConfig has {id, name, color}
   ```

2. **Specify the return contract** for each shared function:
   ```
   // CombatSystem.executeAttack() returns {attackerDamage, defenderDamage, attackerKilled, defenderKilled}
   // BasicAI.decide(state, phase) returns Action[]  (Action has {type, params})
   ```

3. **Require subagents to report their exact API** in the completion summary:
   ```
   // In each subagent context, add: "In your summary, list every public method/class/export
   // with its exact signature so the parent can verify alignment."
   ```

### Post-Merge API Verification (MANDATORY after parallel tracks)

After all tracks complete, BEFORE making any edits to the integrated files:

1. **Re-read all subagent-modified files.** The parent's file cache is stale — subagents may have changed them.
2. **Check for API mismatches** between tracks. The most common drift:
   - Method names differ (`makeDecisions` vs `decide`)
   - Parameter order differs (tribe vs state as first arg)
   - Interface vs class (CityData as `interface` vs using `new CityData(...)`)
   - Constructor arguments differ from what you assumed
3. **Run the build** to surface all type errors at once. Don't try to fix iteratively — collect all errors first, then batch the patches.
4. **Fix all mismatches** before adding new code that depends on these APIs.

**The "re-read before edit" warning from the tool is a critical signal — heed it.** After a subagent writes files, the parent session's cached view is stale. If you edit without re-reading, you overwrite the subagent's work with your (stale) version.

### Stale File Cache Trap

**When the parent session has previously read a file, and a subagent then modifies it, the parent's view becomes stale.** This manifests as:

- Warning messages: `"subagent modified files the parent previously read — re-read before editing"`
- **Silent data loss:** If you write_file without re-reading, you overwrite the subagent's changes with the parent's memory of the file from before the subagent ran.

**The fix — ALWAYS re-read before editing after subagents:**
```python
# WRONG — parent's cached view is stale
patch("src/scenes/GameScene.ts", old, new)  # ❌ Overwrites subagent changes!

# CORRECT
read_file("src/scenes/GameScene.ts")        # ✓ Refresh from disk
patch("src/scenes/GameScene.ts", old, new)  # ✓ Now working with latest
```

**Applies to:** Any file a subagent may have touched, even if the tool warning doesn't fire. If you're not sure whether a file changed, re-read it.

**Example from June 2026 Polytopia clone session:** 3 parallel tracks (entities, turn+AI, combat). Each created independent files. After merge, GameScene.ts had 15+ API mismatches because parent code assumed different signatures than what subagents implemented. Build surfaced them all. Fix: re-read all entity files, correct the GameScene imports/calls to match actual APIs.

**Example from hermes-web-computer (May 2026):**
- Track 1: Go packages (`backend/layout/`, `backend/security/`, `backend/telemetry/`) — 340s
- Track 2: Frontend (`frontend/src/components/`, `frontend/src/stores/`) — 200s (timed out first at 600s with Monaco, succeeded on narrower scope)
- Track 3: Integration (`backend/ws/`, `backend/cmd/`, `deploy/`, `.github/`, `Makefile`) — 343s
- Total: ~6 min vs ~30+ min serial

**When to use parallel mode:**
- Building a new codebase from spec (not modifying existing code)
- Clear file ownership boundaries exist
- Shared interfaces are EXACTLY specified in every subagent's context
- Subagents won't need to read each other's output during execution
- You'll verify integration after all tracks complete

**When NOT to use parallel mode:**
- Modifying existing code (risk of merge conflicts)
- Tasks have interdependencies (Track B needs Track A's output)
- Complex refactoring (serial review catches issues earlier)
- You cannot precisely specify shared type signatures upfront