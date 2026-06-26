# Writing Tasks — Guidelines

Every task in AGENTS.md must be one unit of work for one player tick. This document defines the sizing convention.

## The 2-5 Minute Rule

Each task should take 2-5 minutes of focused implementation work. If it's longer, slice it.

**Too large** (5+ files, multiple subsystems):
```markdown
### Task: fix-strategy-lookup
- **Description**: Fix the strategy lookup endpoint
```

**Right size** (one atomic action):
```markdown
### Task: fix-strategy-lookup-dict-bug
- **Description**: Fix the 'dict' object type bug in get_strategy that causes strategy-lookup to return 500

### Task: seed-preflop-utg
- **Description**: Seed preflop GTO ranges for UTG position at 100bb

### Task: seed-preflop-btn
- **Description**: Seed preflop GTO ranges for BTN position at 100bb
```

## Required Sections

Every task MUST include:

```markdown
### Task: unique-id
- **Description**: One sentence, specific. What to build or fix.
- **Success criteria**: Measurable outcomes. What "done" looks like.
- **Coach checks**: Verification points. What the Coach will check next cycle.
```

## Test Methodology: Expectations First

When a task involves tests, frame it so the Player defines WHAT correct behavior looks like BEFORE writing implementation code. The TDD cycle (RED → GREEN → REFACTOR) must be enforced at the task description level.

✅ Good: *"Define pause/resume expectations from the reference (GDD §X, original app behavior), write failing tests for each expectation, then implement to make them pass"*

❌ Bad: *"Add E2E test for pause/resume"* — this tells the Player to backfill a test for already-written code. The test will validate the implementation, not the requirement.

❌ Bad: *"Write a Playwright test that clicks Escape and verifies overlay"* — this prescribes test mechanics instead of defining expected behavior. The Player implements both test and code in the same context, producing self-referential validation.

**For E2E test tasks specifically:**
- Define expected behavior from an independent reference FIRST (GDD, original site, spec)
- Write the test so it can fail independently of any implementation code
- If the test was written alongside the feature it tests, it's a methodology failure — flag and rewrite

## Success Criteria Examples

| Good | Bad |
|------|-----|
| `curl /api/v1/health` returns 200 | "API is healthy" |
| All 589 tests pass (0 errors, 0 failures) | "Tests pass" |
| Page renders at /study without console errors | "Study page works" |
| Schema migration can be rolled back | "Migration is safe" |

## Coach Checks Examples

| Good | Bad |
|------|-----|
| Verify the new endpoint has auth middleware | "Check security" |
| Confirm schema is backward-compatible | "Check the DB" |
| Test with invalid input, verify 4xx response | "Test edge cases" |

## Prioritisation Order

When generating tasks, order them:

1. **Blocking infrastructure** — API down, proxy broken, deps missing
2. **User-facing blockers** — Study page 500, strategy lookup fails
3. **Data seeding** — API up but no data to serve
4. **Feature gaps** — Pages that exist but are non-functional
5. **Polish** — Loading states, responsive layout, empty states

## Batch Size

Generate 3-5 tasks per batch. No more. The loop generates the next batch when it runs low again.
