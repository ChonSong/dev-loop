# Dev Loop — Autonomous Development System

A multi-loop autonomous development system:
- **Player** agents implement tasks from a backlog
- **Coach** agents adversarially review each commit, probe for gaps, and generate the next batch of tasks
- **Self-Improvement Engine** (SIE) scans every 48h for coverage blind spots, processes learnings, and authors skills

Inspired by g3's dialectical autocoding (Block AI Research, Dec 2025) and built by composing patterns from 10+ existing agent skills.

## Core Concept

Three autonomous loops with increasing cycle times:

```
┌──────────────────────────────────────────────────┐
│              PLAYER/COACH LOOP                   │
│           (every 30m — implementation)            │
│                                                    │
│  AGENTS.md (tasks + criteria)  ──→  Player        │
│       ↑                              │             │
│       │                              ▼             │
│  Coach (reviews, approves,      Checkpoint.json    │
│  probes gaps, generates tasks)  (state tracking)   │
│                                                    │
│  Coach uses delegation to parallelize:             │
│  • External discovery (5 sources)                  │
│  • Spec gap detection (6 independent checks)       │
│  • Live DOM comparison (reference vs clone)        │
└──────────────────────┬───────────────────────────┘
                       │ feeds learnings
                       ▼
┌──────────────────────────────────────────────────┐
│         SELF-IMPROVEMENT ENGINE (SIE)             │
│           (every 48h — meta-improvement)           │
│                                                    │
│  Phase 0: Coverage blind-spot scan (delegates     │
│           per-project audit to subagents)          │
│  Phase 1: Scan .learnings for recurring errors    │
│  Phase 2: Research + author skills                │
│  Phase 3: Commit and push                         │
└──────────────────────────────────────────────────┘
```

Each repo describes itself via `AGENTS.md` + `.checkpoint.json`. The loop discovers repos by scanning for these files.

## How the Agents Were Designed

Both the Player and Coach agents were designed by studying ~12 existing skills in the Hermes ecosystem and extracting their most effective patterns. Here's what inspired each design decision:

### Coach-Agent Inspirations

| Skill | Pattern Borrowed | How It's Used |
|-------|-----------------|---------------|
| **self-improvement-engine** | Weighted scoring formula (`priority × area × recency`) | Adapted to `blocking_weight × confidence` for ranking what task gaps to address first when backlog runs out |
| **parallel-investigation** | Spawn 2-3 subagents, each probing an independent dimension | Used when the Coach needs to check 3+ endpoints/services simultaneously to find what's broken before generating tasks |
| **writing-plans** | 2-5 minute task granularity, exact file paths, verification steps | Each generated task must fit one tick — prevents oversized tasks like "seed strategies" that should be 3-5 smaller ones |
| **planning/blueprint** | "Brainstorm before investigating" — name 2-3 candidates before running probes | Prevents aimless investigation: the Coach already has context from the review and should hypothesize before curling endpoints |
| **planning/product-lens** | ICE scoring (Impact × Confidence ÷ Effort) | Simplified to `blocking_weight × confidence` for the backlog scoring model |
| **adversarial-commitment-audit** | "Don't trust self-report, verify with evidence" | The Coach probes the live system (curl, DB check, browser) rather than trusting the checkpoint's health field |
| **g3 research / evidence-gates** | 8 gates: requirements checklist, compile gate, test gate, edge case gate, security gate, approval sentinel, turn limit, fresh context | Built into the Coach's review protocol as rubber-stamp prevention |
| **doc-driven-dev-loop** | AGENTS.md + checkpoint standard | The format both agents use to discover projects and track progress |
| **evidence-gates (fresh context)** | Coach runs as separate agent with no shared history | This is why the Coach is the right owner for backlog generation — it sees the project fresh every time |

### Player-Agent Inspirations

| Skill | Pattern Borrowed | How It's Used |
|-------|-----------------|---------------|
| **development-communication** | State intent before reading, summarize structure, end-of-tick capture | Player says "reading X to understand Y" before opening files; writes a structured note at end of each tick for cross-session continuity |
| **scrutinize** | End-to-end trace, verify against task criteria before closing | Player does a pre-commit self-review: "does this actually do what the task asked? What will the Coach check?" |
| **test-driven-development** | RED → GREEN → REFACTOR discipline | Every code change starts with a failing test, then minimal implementation, then refactor |
| **writing-plans** | Task size pre-check (2-5 min per unit) | Before starting implementation, Player checks: "can this be done in one tick?" If not, does the minimum slice |
| **spec-audit** | Codebase survey before verifying claims | When the task touches unfamiliar code, Player maps the architecture before touching files |
| **planning/blueprint** | Design tree walk: one question per exchange, resolve blockers first | When success criteria are ambiguous, Player identifies the single decision that unblocks everything and presents a recommendation |
| **adversarial-commitment-audit** | Cross-reference transcript evidence against commitments | Player self-filters: "what evidence will the Coach look for? Do I have it?" before committing |
| **planning/product-lens** | Validate "why" before building | When a task's purpose is unclear, Player pressure-tests before implementing |
| **systematic-debugging** | 4-phase root cause before fixing | When tests fail unexpectedly, Player traces the root cause before proposing a fix |

### Both Agents

| Skill | Pattern | How It's Used |
|-------|---------|---------------|
| **doc-driven-dev-loop** | Per-repo AGENTS.md + checkpoint.json + round-robin scheduling | The foundation both agents operate on |
| **phased-project-runner** | Time budget with hard limits + graceful degradation | Each phase has a target and a hard limit, with a defined fallback when exceeded |

## Quick Start

### 1. Add AGENTS.md to a repo

Copy `templates/AGENTS.md` to the repo root. Fill in:

- **About**: one-line description + status (active/maintenance/legacy)
- **Architecture**: stack, key directories, service relations
- **Conventions**: test commands, lint, commit format, safety rules
- **Skills**: Hermes skills to load for this project
- **Tasks**: ordered by priority, each with success criteria and coach checks

### 2. Add .checkpoint.json

Copy `templates/checkpoint.json` to the repo root. Set `current_task` to the first task ID from AGENTS.md.

### 3. Register in master checkpoint

Copy `templates/master-checkpoint.json` to `~/.hermes/master-checkpoint.json`. Add your project entry.

| 4. Cron jobs handle the rest

The Player cron runs every 30min and picks up any repo with both AGENTS.md + checkpoint. The Coach runs 5 minutes later and reviews. The SIE runs every 48h scanning for coverage blind spots and authoring skills.

## Repository Structure

```
dev-loop/
├── README.md                     # This file
├── docs/
│   ├── architecture.md           # Full loop design (incl. SIE + RSI)
│   ├── agent-roles.md            # Coach and Player responsibilities
│   ├── project-onboarding.md     # Step-by-step project setup
│   ├── scoring-model.md          # Backlog prioritisation formula
│   └── cron-setup.md             # Cron job configuration reference
├── templates/
│   ├── AGENTS.md                 # Blank AGENTS.md
│   ├── checkpoint.json           # Blank checkpoint
│   └── master-checkpoint.json    # Blank master checkpoint
└── skills/
    ├── coach-agent.md                 # Coach role reference
    ├── player-agent.md                # Player role reference
    ├── self-improvement-engine.md     # SIE role reference
    └── writing-tasks.md               # Task writing guidelines
```
