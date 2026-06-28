# Dev Loop — Autonomous Development System

A multi-loop autonomous development system:
- **Grand SIE** (Strategic Intelligence Engine) — the top-layer brain. Scans the external world weekly (GitHub trending, arXiv, competitors, HN), decides what's worth building, and produces requirements specs. See [`docs/grand-sie-architecture.md`](docs/grand-sie-architecture.md).
- **Player** agents implement tasks from a backlog
- **Coach** agents adversarially review each commit, probe for gaps, and generate the next batch of tasks
- **Observation Memory** (`coach_memory.py`) — persistent, self-correcting behavioral knowledge store for the Coach. FTS5 query, trust-scored observations, circuit breaker for safety. Ported from agent-qa's A.U.D.N. curator pattern.
- **Self-Improvement Engine** (SIE) scans every 48h for coverage blind spots, processes learnings, and authors skills. Extended by Grand SIE for outward-facing strategic intelligence.

Inspired by g3's dialectical autocoding (Block AI Research, Dec 2025) and built by composing patterns from 10+ existing agent skills.

## Core Concept

Four autonomous loops with increasing cycle times:

```mermaid
flowchart TB
    subgraph GRAND_SIE["GRAND SIE — STRATEGIC INTELLIGENCE (weekly/biweekly)"]
        direction LR
        RADAR[Opportunity Radar] -->|external signals| SYNTH[Synthesis Engine]
        AUDIT[Self-Audit Engine] -->|internal waste| SYNTH
        SYNTH -->|strategic brief| REQ[Requirements Engine]
        REQ -->|specs + tasks| PLAYER_COACH
    end

    subgraph PLAYER_COACH["PLAYER/COACH LOOP (every 30m)"]
        AGENTS[AGENTS.md] -->|tasks + criteria| Player
        Player -->|implemented code| Checkpoint
        Checkpoint -->|review request| Coach
        Coach -->|reviews, approves, probes gaps| AGENTS
        Coach -->|generates tasks| AGENTS

        subgraph Memory["Observation Memory Layer (coach_memory.py)"]
            direction LR
            BRKR[Circuit Breaker] -->|if not tripped| INDEX[Memory Index]
            INDEX -->|injected context| Coach
            Coach -->|post-review findings| CURATOR[AUDN Curator]
            CURATOR -->|add/confirm/deprecate| STORE[Observation Store]
        end

        Coach -.->|parallelize| D1[External discovery: 5 sources]
        Coach -.->|parallelize| D2[Spec gap detection: 6 checks]
        Coach -.->|parallelize| D3[Live DOM comparison]
    end

    PLAYER_COACH -->|learnings| SIE
    SIE -->|knowledge + patterns| GRAND_SIE

    subgraph SELF_IMP["SELF-IMPROVEMENT ENGINE (every 48h)"]
        P0[Phase 0: Coverage blind-spot scan]
        P1[Phase 1: Scan .learnings for errors]
        P2[Phase 2: Research + author skills]
        P3[Phase 3: Commit + push]
    end
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

## How the Dev Loop Improves Itself

The dev loop is self-referential — it can detect its own gaps, investigate external systems for solutions, and port those solutions back into the loop. The observation memory module is the first example of this.

### The Gap

The Coach had no persistent memory. Every session started cold — same UI quirks, same async load patterns, same flaky selectors had to be rediscovered. The `memory` tool and `session_search` stored unstructured notes, but there was no behavioral knowledge store the Coach could query before a review or update after one.

### The Investigation

We identified [vostride/agent-qa](https://github.com/vostride/agent-qa) — an open-source LLM-powered E2E testing harness whose core agent loop closely mirrors the Coach/Player architecture. The full investigation:

1. **Repository reconnaissance** — cloned the 144★ TypeScript monorepo, mapped its 9 packages (core, cli, web, android, ios, mcp, ids, dashboard-server, dashboard-ui)
2. **Architecture extraction** — read 10 key source files totaling 150KB+ (loop.ts 39KB, curator.ts 24KB, runner.ts 32KB, agent-qa-server.ts, verifier.ts, planner.ts, circuit-breaker.ts, similarity.ts, memory-index.ts, file-cache.ts)
3. **Pattern documentation** — extracted 10 architectural patterns into `coach-agent/references/agent-qa-architecture.md`, with applicability assessment and priority ranking for our loop
4. **Comparison mapping** — identified what agent-qa does that we don't (memory curator, action cache, verifier phase, circuit breaker) and what we do that agent-qa doesn't (multi-agent delegation, skill system, cron pipeline)

### The Port

Three patterns were immediately actionable and directly ported — the remaining seven are documented for future work:

| Pattern | Ported | File | Key Mechanism |
|---------|--------|------|---------------|
| **A.U.D.N. Curator** | ✅ | `curator.py` | LLM evaluates each review, makes Add/Update/Deprecate/Noop decisions. Auto-deprecates injected observations on failure. Trust scoring 0-1. |
| **Circuit Breaker** | ✅ | `circuit_breaker.py` | 20-run rolling window per project. Trips when memory-wrapped runs fail 15% more than baseline. Stays tripped until fixed. |
| **Failure Classifier** | ✅ | `classifier.py` | Rule-based 7-needle priority matcher. No LLM call. 8 categories from timeout to infrastructure. |
| **FTS5 Memory Index** | ✅ | `index.py` | Stopword-stripped OR queries for high recall. Similarity fallback. Trust-weighted ordering. |
| **Jaccard Dedup** | ✅ | `similarity.py` | Title-aware 0.85 threshold. Prevents observation bloat without an LLM call. |
| Action Cache | 📋 | — | Sub-action cache with prefix invalidation. Lower priority — needs Player integration. |
| Verifier Phase | 📋 | — | Separate LLM check after stepComplete. Needs Player integration. |
| Secrets Redaction | 📋 | — | Required if caching sub-actions with embedded secrets. |
| Memory Depth Tiers | 📋 | — | Already partially handled (product/task/suite in store.py). |
| Forced Tool Calls | 📋 | — | Deeper change to how Player generates actions. |

### The Build

The port itself followed the dev loop pattern: the Coach investigated (this README section documents that investigation), identified the work, and the implementation was done in a single focused session — ~90 minutes from repository discovery to merged commit. Each component was tested in isolation (pytest-style assertions in `cli.py`), then integrated end-to-end, then pushed as runnable code.

The meta-lesson: **the dev loop can improve itself.** When the Coach notices a systemic gap (like "I keep rediscovering the same facts"), it can research external projects, extract the solution pattern, and build it — turning an expensive recurring problem into a solved one.

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
│   ├── architecture.md           # Full loop design (incl. SIE + RSI + E2E layer)
│   ├── agent-roles.md            # Coach and Player responsibilities
│   ├── project-onboarding.md     # Step-by-step project setup
│   ├── scoring-model.md          # Backlog prioritisation formula
│   ├── cron-setup.md             # Cron job configuration reference
│   ├── e2e-infrastructure.md     # E2E test infra: POM design, file layout, agent resp.
│   ├── grand-sie-architecture.md # Grand SIE: Opportunity Radar + Requirements Engine (Phase 1-2)
│   ├── observation-memory.md     # Observation memory: curator, breaker, classifier
├── observation_memory/           # Python library: store, index, curator, breaker, classifier, similarity
├── coach_memory.py               # Coach integration CLI (inject, curate, classify, breaker)
├── enforce_qa_gate.py            # Post-cycle gate — rejects rubber-stamp approvals
├── scripts/
│   ├── opportunity-radar.py       # Grand SIE Phase 1 — external signal scan
│   └── self-audit.py              # Grand SIE Phase 1.5 — inward system audit
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
