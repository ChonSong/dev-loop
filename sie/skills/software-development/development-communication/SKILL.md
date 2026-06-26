---
name: development-communication
description: "Keep the user informed during development work — state intent before reading files, summarize structure before editing, explain location choices, surface delegation work, call out surprises. Covers cross-cutting transparency norms for all development sessions. Trigger on ANY development/build/debug work — not just planning or debugging."
version: 1.0.0
author: Sean Cheong / OWL
license: MIT
metadata:
  hermes:
    tags: [communication, transparency, development, workflow, collaboration, session-closure, logging, skills-research]
    related_skills: [writing-plans, systematic-debugging, subagent-driven-development]
---

# Development Communication

## Overview

Be a transparent collaborator during development, not a black box that silently produces output. The user should always know what you're looking at, what you found, and why you're making each change.

**Core principle:** Every file read, every edit choice, every delegation is visible. The user follows the journey, not just the destination.

## Reading Files

- **State intent before reading:** "Reading `services/auth.ts` to understand the login flow"
- **After reading 3+ files:** Summarize — "I looked at the routing (3 files), the middleware chain, and the auth service. Here's what I found..."
- **When building context for unfamiliar code:** "I'm new to this codebase, let me map it out first" — then give a quick structural summary before any analysis

## Making Changes

- **Reference specific files and line ranges:** Not "I updated the service layer" but "Modified `api/handlers.go:42-67` to add input validation"
- **Explain location choices:** "Putting this in `utils/validation.ts` because it's shared by both `/auth` and `/user` routes"
- **Before touching 3+ files:** "Here's what I'm about to change and why" — a brief pre-execution summary
- **Note:** Plans should be presented before execution, not just saved to `docs/plans/` silently

## Exploring Codebases

- **Unfamiliar codebases:** Provide a quick structural map before proposing changes
  - Key entry points and their roles
  - Directory layout and conventions
  - Notable patterns or gotchas you found
- **Call out surprises:** Unexpected dependencies, weird patterns, stale dead code, naming inconsistencies — flag them, don't silently work around them
- **State confidence level:** "I *think* `router.ts` is the main routing layer, but the middleware ordering is unusual — let me verify before I propose changes there"

## Delegating Work

- **Default to parallel** for multi-part tasks with 2+ independent workstreams — dispatch all sub-tasks simultaneously via `delegate_task(tasks=[...])`  
  **Current reality: 0% of subagent sessions run in parallel.** Config allows 3 concurrent — batch dispatch is pure free wall-clock speedup.
- **Tell the user what each subagent is doing:** "Spawning 3 parallel subagents to investigate: (A) benchmark lifecycle, (B) test tooling, (C) GitHub secrets"
- **Surface subagent structural findings:** Don't silently fold them in — report what the subagent discovered about the codebase
- **Report subagent completion with what was touched:** "Subagent finished — modified 4 files in `src/auth/`, all tests passing"

### Mandatory: Collate Parallel Results

After parallel subagents return, ALWAYS synthesize their output into a cross-stream analysis:

```
## Parallel Findings

### Stream A: [topic]
Key finding: ...
Recommendation: ...

### Stream B: [topic]
Key finding: ...
Recommendation: ...

### Synthesis
Cross-stream patterns: ...
Recommended next action: ...
```

Raw subagent output is not the deliverable. The user gets a single synthesized view with decisions/recommendations, not three separate reports to read.

## Skills Research (Investigating Existing Skills for Patterns)

When researching multiple skills to compose a solution, output findings as a **structured table** — not prose paragraphs.

### Workflow

1. **List candidates**: `skills_list()` the relevant categories
2. **Load each**: `skill_view()` full content
3. **Extract**: For each skill, identify the single pattern most relevant to the current problem
4. **Output table**:

```markdown
## Findings Across N Skills

| Skill | Key Pattern | How Adapted | What It Prevents |
|-------|-------------|-------------|------------------|
| `skill-a` | Scoring algorithm | Adapted to X scenario | Guesswork prioritisation |
| `skill-b` | Design tree walk | One decision per exchange | Ambiguous requirements |
| `skill-c` | 2-5 min granularity | Task size pre-check | Oversized tasks |
```

5. **Assess coverage**: Which gaps remain after composing existing skills?

### Why This Format

- The user can scan the table in seconds to see what was considered
- Clear mapping from each skill to the borrowed pattern
- Explicit "what it prevents" shows the reasoning
- Coverage gaps are immediately visible (missing rows = missing patterns)

### Anti-Pattern

- Listing skills without extracting their patterns: "I looked at blueprint, writing-plans, and parallel-investigation" — what did you *learn* from each?
- Presenting findings as unbroken prose paragraphs — user has to re-read to extract the structure

## Brevity Scaling

- **Quick tasks (1-2 files, obvious fix):** Terse is fine — "Fixed the null check in `utils.ts:34`"
- **Development work (3+ files, unfamiliar territory):** Narrate. Reference files, state intent, explain reasoning
- **The rule:** Brevity scales with familiarity. Building together means narrating the journey.

## Anti-Patterns

### Black Box (Don't Do This)
- Reads 5 files silently
- Outputs "Done, I fixed the auth bug"
- User has no idea what changed or why

### Empty Response After Tool Calls (CRITICAL — Don't Do This)
- Executes 5+ tool calls that produce meaningful results (file contents, error messages, build output)
- Returns nothing — silence, empty string, or ends turn without any narrative
- User receives tool output with no framing, no diagnosis, no decision
- This is the WORST communication failure: the most work for the least clarity. The user sees raw tool output and has to reconstruct intent.

**Always conclude any tool execution block with a narrative response.** After the last tool result comes in, synthesize what was found, state the decision, and what happens next. Even a one-line summary is better than silence.

### Verbose Overload (Also Don't Do This)
- Narrating every single `read_file` call for a trivial 2-line fix
- "I'm now reading line 45. Now I'm reading line 46."

### Right Level
- "Reading the auth service and middleware to trace the login flow"
- "Found the issue: `validateToken()` in `auth/middleware.ts:78` returns `void` instead of `bool`. Fixing."
- "Spawning subagent to refactor the DB layer — will report back with what it touches"

## During Debugging

Pair with `debug-first-fix-never` discipline:

1. State what you're examining and why
2. Report what you found (even if it's "nothing unusual")
3. State your hypothesis before touching code
4. Show the diff or change location before/after running

## During Planning

Pair with `writing-plans` discipline:

- Present the plan before executing
- For 3+ file changes: "Here's what I'm about to touch" summary
- Explain architectural decisions, don't just list tasks

## End of Session — Logging & Continuity

**Before any session ends** (or when context runs low), close the loop on what was accomplished.

### Mandatory: Write the Daily Log

After any non-trivial session (5+ tool calls, project work, errors overcome):

1. **Write** `memory/YYYY-MM-DD.md` with structured sections:
   ```markdown
   # YYYY-MM-DD — [Topic]
   ## [Major Work Stream]
   ### Actions / Decisions
   ### Files Changed
   ### Pending
   ```
2. **Check for multiple work streams** — did you switch between projects? E.g. GTO Wizard deploy + HWC investigation on the same day. Each stream gets its own `##` section. **Pitfall: logging only one stream when you worked on multiple is the same as not logging the rest.**
3. **Log all findings, even if partial** — unfinished investigation, deferred tasks, known gaps all go in the "Pending" section of that stream.

### Pitfall: Session-Amnesia

The cost of NOT logging is that the next session starts blind — re-reading files, re-discovering bugs, re-building context from scratch. **Writing the log before session end is cheaper than reconstructing via session_search later.**

If you're low on context or hitting the model limit:
- Write a terse log first — even 5 bullet points per stream — then expand next session
- Set a cron or reminder if the work genuinely needs follow-up

### Verification

After writing the log, confirm it exists with content. If you caught yourself about to close without logging, that's the exact scenario this section exists to prevent.
