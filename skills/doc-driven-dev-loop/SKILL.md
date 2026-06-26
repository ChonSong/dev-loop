---
name: doc-driven-dev-loop
description: "Set up and maintain the doc-driven autonomous development loop: per-repo AGENTS.md + checkpoint.json standard, player/coach adversarial review, round-robin scheduling, skills wiring, and ongoing audit. Load this skill when onboarding a project or debugging the loop."
tags: ["autonomous", "dev-loop", "coach-player", "adversarial", "agentes-md", "g3"]
related_skills: ["player-agent", "coach-agent"]
---

# Doc-Driven Autonomous Development Loop

## Overview

Each repo self-describes its work via AGENTS.md + .checkpoint.json. A **player** cron job executes tasks from the backlog. A **coach** cron job (offset by 5m) reviews each commit against success criteria with fresh context. A daily memory curation cron audits all projects.

Inspired by g3's adversarial cooperation pattern (Block AI Research paper, Dec 2025): a coach/player feedback loop where the coach spawns with fresh context and evaluates against the original requirements, preventing self-report rationalization.

## Onboarding a New Project — Step by Step

### 1. Investigate the Codebase First
Before writing AGENTS.md, understand the project:
- Architecture, stack, key directories
- Test framework and whether tests actually run
- Current git log (recent commits, conventions)
- Existing documentation (README, SPEC, AGENTS.md)
- What end-user value the project delivers

### 2. Write AGENTS.md

Required sections:

```markdown
# AGENTS.md — [project-name]

## About
One-line description + current status: active | maintenance | legacy | experiment

## Architecture
- Stack (language, framework, database)
- Key directories and what they contain
- How services relate (API → solver → DB, etc.)

## Conventions
- Testing requirements (pytest, vitest, e2e)
- Linting/code style (ruff, prettier, eslint)
- Commit message format
- Anything an agent must know to work safely here

## Skills
Hermes skills to load when working on this project.
The cron job loads these automatically — do NOT tell agents to load them dynamically.
| Skill | When | Why |
|-------|------|-----|
| `skill-name` | What task types need it | Why it helps |

## Tasks

Ordered by priority. Each task is ONE unit of work for ONE player tick.

### Task: unique-task-id
- **Description**: What to build/fix
- **Success criteria**: Measurable outcomes — "all tests pass", "API responds 200 for X", "new page renders at /path"
- **Coach checks**: Specific things the coach verifies — "schema migration is backward-compatible", "new endpoint has auth middleware"
- **Skills**: Task-specific skills beyond project defaults (optional)
```

### 3. Write .checkpoint.json

```json
{
  "project": "project-name",
  "repo": "/home/sc/repos/project-name",
  "current_task": "first-task-id",
  "completed": [
    {"task": "task-id", "sha": "abc1234", "date": "2026-06-15", "coach": "approved"}
  ],
  "health": "tests_pass|tests_fail|unknown",
  "last_sha": "abc1234",
  "blocker": null
}
```

### 4. Update Master Checkpoint

```json
{
  "last_run": "2026-06-15T10:00:00Z",
  "consecutive_on_project": 0,
  "active_project": "project-name",
  "projects": {
    "gto-wizard-clone": {
      "status": "active",
      "priority": 1,
      "current_task": "first-task-id",
      "health": "tests_unknown",
      "last_sha": "abc1234",
      "blocker": null
    }
  }
}
```

Dead entries (projects with "repo not found" blockers) should be removed, not preserved.

### 5. Write Agent Skills

Two skills must exist in ~/.hermes/skills/:

**player-agent**: Implementer role — one task per tick, tests before commit, round-robin awareness.
**coach-agent**: Adversarial reviewer — DECISION: APPROVE/FIX/REVERT with evidence requirements.

Both are loaded by cron jobs via the `skills: [...]` field, not dynamically at runtime.

### 6. Set Up Cron Jobs

**Player** (every 60m at `0 * * * *`):
- Skills: `["player-agent"]`
- Prompt: minimal per-tick instruction (the skill does the heavy lifting)
- Toolsets: `["terminal", "file", "web"]`
- Model: fast/cheap (deepseek-v4-flash or equivalent)

**Coach** (every 60m at `5 * * * *`):
- Skills: `["coach-agent"]`
- Prompt: minimal per-tick instruction
- Should use a STRONGER model than the player for rigorous review (claude-sonnet-4-5, gpt-5.4-codex, etc.)
- Toolsets: `["terminal", "file"]`

### 7. Wire Ongoing Audit

The daily memory curation cron (at `0 16 * * *`) should have toolsets `["search", "file", "terminal"]` and:
- Walk all projects with AGENTS.md + checkpoint.json
- Check progress (commits since last SHA, by agent role)
- Flag stalled tasks (>48h on same current_task)
- Evaluate coach quality (APPROVE/FIX/REVERT pattern — is coach rubber-stamping?)
- Write audit to curation logs

## AGENTS.md Task Design Principles

**Success criteria** must be:
- Measurable: "Tests pass", "API returns 200", "Page renders without console errors"
- Verifiable: The coach can check each one independently
- Bounded: Achievable in a single player tick
- Not vague: Avoid "Improve quality" or "Polish UI" without specifics

**Coach checks** should be:
- Security-aware: "Auth is enforced", "Input is validated"
- Regression-aware: "Existing tests still pass", "Schema is backward-compatible"
- Evidence-based: The coach checks these with curl, test runs, or diff inspection

## Pre-Flight Plan Discipline (g3-inspired)

Before implementing ANY task, the player writes a mini-plan with four parts:

| Part | What | Example |
|------|------|---------|
| **Touches** | Files/modules expected to modify | `apps/api/routers/strategy_lookup.py, apps/api/services/strategy_storage.py` |
| **Happy path** | What success looks like and how to verify | `GET /api/v1/strategy/lookup?position=UTG returns 200 with valid strategy JSON` |
| **Negative path** | Error handling — at least one | `GET with missing position returns 400` |
| **Boundary/edge case** | Limits, empty input, max values — at least one | `GET with unknown position returns 404` |

This prevents scope creep, happy-path-only implementations, and rushing to code without understanding the codebase. The plan is output as a code block before the first implementation tool call.

This is embedded in `player-agent`'s Pre-Flight Plan Discipline section and enforced as workflow step 5.

## Scout Agent for Bounded Research

When task context is insufficient (unfamiliar library, ambiguous requirements, unknown codebase), the player loads `scout-agent` to produce a bounded 1-page research brief before planning. The scout follows g3's output contract:

```
---SCOUT_REPORT_START---
Query, Options, Trade-offs, Recommendation, Unknowns, Sources
---SCOUT_REPORT_END---
```

This prevents aimless exploration and forces decision-ready output. The scout-agent skill lives at `/home/sc/.hermes/skills/scout-agent/SKILL.md`.

## Key Learnings from g3 Implementation

See `references/g3-architectural-comparison.md` for a detailed comparison of g3's shared-session approach versus our separate-cron approach, including trade-offs and when each works better.

### Coach/Player Loop Mechanics (from g3 Rust source)

1. **Fresh context per coach turn**: Coach spawns as a completely new agent with no context bleed from the player. Our separate cron jobs achieve this automatically. g3 achieves it by rebuilding the agent from scratch in `autonomous.rs`.

2. **Approval sentinel**: Coach must output an unambiguous structured decision, not prose. g3 uses `IMPLEMENTATION_APPROVED`. We use `DECISION: APPROVE / FIX / REVERT` as the first line of the verdict.

3. **Player errors surface via full output**: Coach sees everything the player ran (stdout, stderr, exit codes, diff output). There is no separate error channel — the coach reviews the full artifact.

4. **Rejection = retry, not escalate**: On rejection, the same player task gets iterated with coach feedback. No human escalation path. Circuit breaker is max turns (g3 defaults to 10; our separate cron jobs naturally limit this since each tick is one attempt).

5. **Separate model per role**: g3 configures different providers/models for coach and player via `config.coach-player.example.toml`. Coach uses lower `max_tokens` (32000 vs 64000) and is optimized for evaluation, not generation.

### Evidence Gates (Preventing Rubber-Stamping)

From g3 and the adversarial cooperation paper, effective gates are:

1. **Requirements checklist** — each criterion individually checked with ✅/❌ and specific gap notes
2. **Compilation gate** — does it compile/run?
3. **Functional test gate** — test actual behavior, not just compilation
4. **Edge case gate** — negative and boundary cases, not just happy path
5. **Security gap checklist** — auth, HTTPS, input validation, error handling
6. **Approval sentinel** — explicit structured output required
7. **Fresh context per coach turn** — prevents rationalization
8. **Feedback specificity requirement** — feedback must be substantive, not generic

### Preventing Coach Rubber-Stamping

1. **Fresh context**: Coach never inherits player's context — starts clean every turn
2. **Requirements anchoring**: Coach evaluates against the AGENTS.md criteria, NOT the player's commit message
3. **Explicit threshold**: Coach's bar is "all criteria met", not "looks good"
4. **Coach optimized for evaluation**: Different model config (lower temperature, structured output)

## Backlog Curation (Preventing Silent Stalling)

The most common failure mode of the dev loop is exhausting the AGENTS.md task list while user-facing features remain broken. The loop stops making progress silently — no error, no alert, just `current_task: tbd`.

### Who Owns Backlog Generation

**Primary: the Coach.** At the end of each review tick, the Coach checks remaining unstarted tasks in AGENTS.md. If < 2 remain, it investigates what's broken (curl endpoints, check DB, browser test) and generates 3-5 new tasks. The Coach has freshest context and uses the stronger model.

**Secondary: the Player.** The Player checks remaining tasks at the START of each tick. If 0 remain, it triggers Task Exhaustion Recovery. This catches cases where the Coach failed to generate tasks (crashed, timed out, model failure).

### Skills to Compose for Backlog Investigation

| Skill | When to Use |
|-------|-------------|
| `scout-agent` | Insufficient task context — research libraries, APIs, or approaches before implementing. Produces bounded 1-page brief with options and trade-offs |
| `parallel-investigation` | Spawn 3 subagents simultaneously to probe API health, DB state, and browser errors |
| `software-development/writing-plans` | Task granularity convention (2-5 min each, exact file paths, verification steps) |
| `planning/blueprint` | When a new task is itself a multi-step feature that needs decomposition |
| `player-agent` → Task Exhaustion Recovery | Secondary/failsafe when Coach misses backlog generation |

## Research-Reference Pattern

When asked how to solve a design or architecture problem, the correct first step is to **research how an existing implementation handles it** — before proposing any solution. This session's g3 investigation taught us the coach/player loop, plan system, scout agent, and model separation patterns.

The general pattern: **Research → Synthesize → Design → Implement**, not Design → Implement.

## Skills-First Approach

Before proposing any architectural or design solution for a dev loop problem, **research what existing skills already cover the territory.** This prevents:

- Proposing patterns that already exist as skills (waste)
- Missing pitfalls already documented in existing skills (repetition)
- Suggesting approaches that conflict with existing skill designs (incompatibility)

### Workflow

When asked how to solve a dev loop problem:

1. **skills_list()** the relevant categories (`autonomous-ai-agents`, `planning`, `software-development`, `devops`)
2. **skill_view()** the 3-5 most promising candidates
3. **Assess what already exists** — which skill directly addresses the problem, which needs a minor patch, which is irrelevant
4. **Only then propose** — your proposal should name which existing skills to compose and what gap needs a new addition

Example from session 2026-06-16: User asked "how should we add backlog curation to the loop." Instead of jumping to "create a new backlog agent", I should have first loaded `parallel-investigation`, `blueprint`, `writing-plans`, `player-agent` (Task Exhaustion Recovery), and `coach-agent` — finding that `coach-agent` extension was the minimal change that composes best with existing skills, rather than proposing a new cron job.

## Pitfalls (from implementation)

- **Skills are loaded at cron start, not dynamically**: Do NOT tell the agent to "load skills if AGENTS.md has them" — that's impossible mid-session. The cron job's `skills: [...]` field handles this at job start.
- **One task per tick**: Don't chain tasks. If a task is too large, split it in AGENTS.md backlog.
- **Tasks exhausted = silent death**: Now mitigated by Coach backlog curation (primary) + Player proactive check (secondary). If both fail, the daily memory curation audit catches it. Monitor `projects.<name>.current_task` in the master checkpoint — if any project has `"tbd"` for >48h, flag it.
- **Don't touch AGENTS.md format**: The player should never modify AGENTS.md structure. The coach validates against it. Only the user or a dedicated task should update it.
  - **EXCEPTION**: When tasks are exhausted AND user-facing features are broken, adding the next set is the right thing to do. See `player-agent` → "Task Exhaustion Recovery" for the procedure.
- **Tests before commit**: If the test environment is broken, fixing it IS the first task. Never commit untested code.
- **Coach model matters**: If the coach uses the same model as the player, it tends to rubber-stamp. Always use a stronger model or add structural evidence requirements.
- **Dead checkpoint entries**: Projects with "repo not found" blockers consume attention. Remove them from the master checkpoint.

## Non-Blocking Review Mode (Interactive User)

When a human user is actively co-developing (not hands-off autonomous), use this variant:

### How It Works
1. **Living spec document** (`GDD.md`, `SPEC.md`, or `DESIGN.md`) lives in the repo — separate from AGENTS.md.
   - AGENTS.md = task backlog + conventions
   - GDD.md = full specification with section numbers
2. **Tasks reference spec sections.** Every task entry says `GDD §X: description` so the implementation is traceable.
3. **Pipeline never blocks.** The agent works through tasks in order. Each task = one commit + deploy.
4. **User reviews asynchronously.** They check the live site, read commit messages, play with the output.
5. **User redirects by editing files.** They modify GDD.md (change spec) or AGENTS.md (reorder/add/block tasks). The agent reads these files fresh each task and adapts.
6. **No interrupt messages needed.** The user doesn't have to say "stop" or "change direction" — editing the task/spec files IS the signal.
7. **E2E tests as coach.** For projects with a user-facing interface (game, web app, API), write Playwright/Cypress tests that simulate real user interaction. These are the automated "coach" — they catch regressions the unit tests miss.

### Spec Document Structure (GDD.md / SPEC.md)
```
# GDD.md — [Project Name]: Living Game/Product Design Document

> Status: Active — source of truth for all mechanics/features.
> Change process: Tasks in AGENTS.md reference specific GDD sections.
> When the spec changes, update GDD.md first, then update AGENTS.md tasks.

## 1. Section
### 1.1 Subsection
- Fact
- Value
```

### Checklist for This Mode
- [ ] Is there a GDD.md/SPEC.md in the repo?
- [ ] Do AGENTS.md tasks reference spec sections (e.g. "GDD §4.1")?
- [ ] Are E2E tests written that simulate real user interaction?
- [ ] Does the user know they redirect by editing GDD.md / AGENTS.md?
- [ ] Are commits self-contained (one feature, one section, one commit)?

## AGENTS.md Task Design Principles

**Success criteria** must be:
- Measurable: "Tests pass", "API returns 200", "Page renders without console errors"
- Verifiable: The coach can check each one independently
- Bounded: Achievable in a single player tick
- Not vague: Avoid "Improve quality" or "Polish UI" without specifics
- **Spec-referencing**: Reference the exact GDD section (e.g. "Implement §4.1 damage formula")

**Coach checks** should be:
- Security-aware: "Auth is enforced", "Input is validated"
- Regression-aware: "Existing tests still pass", "Schema is backward-compatible"
- Evidence-based: The coach checks these with curl, test runs, or diff inspection

## Non-Blocking Review Key Principle

> **The user edits spec/task files to redirect. The pipeline never stops.**
> 
> This is the opposite of request-response development where the user must send a message to change course. In this model:
> - GDD.md changes = "the spec is now different, next task should reflect that"
> - AGENTS.md task reorder = "work on this next"
> - AGENTS.md `⚠️ BLOCKER` note = "investigate before proceeding"
> 
> The agent reads the current state of these files at the start of each task. No message required.

## AGENTS.md File Locations

| File | Path | Purpose |
|------|------|---------|
| GTO Wizard | `/home/sc/repos/gto-wizard-clone/AGENTS.md` | First project onboarded |
| Polytopia Clone | `/home/sc/repos/polytopia-clone/AGENTS.md` | Game project with GDD.md pattern |
| Player skill | `/home/sc/.hermes/skills/player-agent/SKILL.md` | Implementer role |
| Coach skill | `/home/sc/.hermes/skills/coach-agent/SKILL.md` | Adversarial reviewer role |
| Dev loop repo | `ChonSong/dev-loop` (private) | Canonical reference: AGENTS.md template, scoring model, cron setup, onboarding guide |
| Design doc | `/home/sc/workspace/design/dev-loop-v2.md` | Initial design reference |
