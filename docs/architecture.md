# Architecture

## Overview

The dev loop implements a **dialectical autocoding** pattern — two agents with different roles, different models, iterating on the same work, plus a meta-loop for self-improvement. The Player implements, the Coach adversarially reviews, and the Self-Improvement Engine (SIE) closes the gap between "logged a learning" and "built the skill."

## Data Flow

```
                      ┌─────────────────────────────┐
                      │     Master Checkpoint        │
                      │  (~/.hermes/master-          │
                      │   checkpoint.json)           │
                      └──────────┬──────────────────┘
                                 │ reads/writes
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                   ▼
     ┌────────────────┐  ┌─────────────────┐  ┌──────────────┐
     │  Player Cron   │  │  Coach Cron     │  │  SIE Cron    │
     │  (every :00/30)│  │  (every :05/35) │  │  (every 48h) │
     │                │  │                 │  │              │
     │ Flash model    │  │ Same model +    │  │ Scans        │
     │                │  │ delegation for  │  │ coverage,    │
     │                │  │ parallel probes │  │ authors      │
     │                │  │ (5-6 subagents) │  │ skills       │
     └───────┬────────┘  └────────┬────────┘  └──────┬───────┘
             │                    │                    │
             ▼                    ▼                    ▼
     ┌─────────────────────────────────────────────────────┐
     │                  Per-Project Repos                    │
     │  ┌───────────────────────────────────────────────┐   │
     │  │  AGENTS.md  │  .checkpoint.json  │  src/      │   │
     │  └───────────────────────────────────────────────┘   │
     └─────────────────────────────────────────────────────┘
                            │
                            ▼
     ┌─────────────────────────────────────────────────────┐
     │                  Learning Layer                       │
     │  hermes-sync/memory/.learnings/                      │
     │  • LEARNINGS.md   • ERRORS.md   • FEATURE_REQUESTS  │
     │  SIE Phase 0 scans gaps → seeds entries → pipeline   │
     └─────────────────────────────────────────────────────┘
```

## Three Loops + E2E Test Layer

| Loop | Frequency | Role | Tests Run | Toolsets Include |
|------|-----------|------|-----------|-----------------|
| **Player** | Every 30min (:00) | Implements one task | `pytest`, `vitest` (+ e2e POM update if UI change) | terminal, file, web |
| **Coach** | Every 30min (:05) | Reviews commits, probes gaps, generates tasks | `pytest`, `vitest`, **`npm run test:e2e`** | terminal, file, web, browser, session_search, **delegation** |
| **SIE** | Every 48h | Scans coverage blind spots, authors skills | Scans for **e2e existence + freshness** | terminal, file, **delegation** |

**E2E test flow across loops:**

```
Player implements feature
  │  pre-flight: check if page has e2e tests
  │  if yes: update POM + spec
  ▼
Commit + push
  │
Coach reviews
  │  1. pytest + vitest
  │  2. npm run test:e2e ← Layer 3
  │  3. if fail: classify (known bug vs regression)
  │  4. if recurring pattern: seed .learnings entry
  │  5. verdict with e2e results
  ▼
SIE Phase 0 (every 48h)
  │  scans all projects for:
  │  • e2e tests exist?
  │  • e2e tests pass?
  │  • POM selectors fresh?
  │  seeds .learnings if gaps found
  ▼
SIE Phases 1-4
  │  promotes recurrences → skill authoring
  ▼
coach-test-generator skill improves
```

## Delegation in the Coach

The Coach uses `delegate_task` to run independent probes in parallel (up to 3 concurrent subagents). This cuts probe time from ~330s serial to ~90s wall-clock:

### Parallelized Probe Phases

**Phase 2.5 — Spec Gap Detection (6 checks):**
| Check | Subagent Toolset | What It Does |
|-------|-----------------|-------------|
| A — Route inventory | file | find page.tsx files, check sizes |
| B — API inventory | file | grep route definitions |
| C — Component detection | file | count imports vs exports |
| D — Reference audit | file, browser | vision_analyze reference images comparison |
| E — Stub sweep | file | grep TODOs across pages |
| F — Velocity check | file | read checkpoint history |

**Phase 2.6 — External Discovery (5 sources):**
| Source | Subagent Toolset | What It Does |
|--------|-----------------|-------------|
| Session histories | session_search | past unaddressed asks |
| GitHub issues | (MCP) | open issues + stale PRs |
| Web research | web | 3x web_search for competitor features |
| Repo catalog | file | cross-reference planned features |
| YouTube | web | search for inspiration (optional) |

### Delegation Constraints
- Max 3 concurrent subagents per cron tick
- Subagents are leaf agents (cannot re-delegate)
- Each gets `enabled_toolsets` tailored to its probe (not the full Coach toolset)
- Results are collated into a single gap scoring pool

## Self-Improvement Engine

The SIE is the meta-loop. It replaces the reactive "log an error → maybe fix it" pattern with a proactive scanning approach.

### Phase 0: Coverage Blind-Spot Scan (LLM-driven)
Before running the Python pipeline, the SIE proactively discovers what the system is NOT checking:

1. Read master checkpoint → discover all projects
2. Delegate per-project audit to subagents (one per project, parallel):
   - Check if a health audit exists for this project
   - Check if the audit covers code quality (or just deployment health)
   - Check last_review freshness
3. Seeds `.learnings/` entries for each uncovered or stale gap
4. Then runs Phases 1-4 pipeline

### Phase 0 Delegation Pattern
```
Master Checkpoint → [subagent for project A,
                     subagent for project B,
                     subagent for project C]
                          ↓
Each subagent: reads audit outputs, classifies posture
                          ↓
Collate results → seed .learnings/ entries
                        ↓
              Python pipeline (Phases 1-4)
```

### Phases 1-4: Python Pipeline
Phases 1-4 are a Python script (`self_improvement.py`), not LLM-driven. They scan `.learnings/` for recurring error patterns, score candidates by severity, research the problem space, and author SKILL.md files.

## RSI Meta-Problem Fix (2026-06-22)

The core RSI bottleneck was identified: **every autonomous loop optimizes for its stated goal and never asks "what should I be checking that I'm not checking?"**

### What Changed

| Problem | Fix |
|---------|-----|
| No loop scans for coverage gaps | SIE Phase 0 now proactively audits all projects |
| Health audit outputs are read by nobody | SIE reads them, classifies coverage, seeds gaps |
| Gaps require manual .learnings/ seeding | Gaps are auto-discovered from master checkpoint |
| Each loop blind to others' blind spots | One meta-loop correlates coverage across all loops |
| SIE only processes what it's told | SIE discovers what it should process |

### Meta-Reflection in Audit Jobs
All LLM-driven audit jobs (HWC Health Audit, etc.) now end with a meta-reflection step: after completing standard checks, the audit asks itself "is there anything this audit should be checking that it doesn't currently?" and seeds a `.learnings/` entry if it finds a gap. This prevents the Goodhart ceiling where benchmarks pass but real problems go undetected.

## Cron Timeout Model

Cron jobs use an **inactivity-based timeout**, not a wall-clock cap:
- **Default**: 600s (10 min) of inactivity — job runs indefinitely as long as it's making tool calls or receiving stream tokens
- **Override**: `HERMES_CRON_TIMEOUT` env var; `0` = unlimited
- **Protected toolsets** (always disabled in cron context): `cronjob`, `messaging`, `clarify`
- **delegation is NOT blocked** — available if included in `enabled_toolsets`

## Project Discovery

The loop discovers projects dynamically by scanning `/home/sc/repos/*/AGENTS.md`. Only repos with BOTH `AGENTS.md` and `.checkpoint.json` get cycles.

## Round-Robin Scheduling

Projects are prioritised by the `priority` field in the master checkpoint. Max 2 consecutive ticks on any project, tracked via `consecutive_on_project` counter. Prevents one project from monopolising all cycles.

## Task State Machine

```
AGENTS.md: Task: [id]  ──→  Player picks it up
                              │
                              ▼
                         Implementation
                              │
                              ▼
                         Tests pass?
                         ├── Yes ──→ Commit
                         └── No  ──→ Fix or revert
                              │
                              ▼
                    Coach reviews
                    ├── APPROVE ──→ checkpoint: {"coach": "approved"}
                    ├── FIX     ──→ corrective commit → approved
                    └── REVERT  ──→ git revert → task stays current

                    When tasks run low (< 2 remaining):
                    Coach generates next batch
```

## Backlog Health Check

The Coach checks remaining task count at the end of each review:

- **≥ 3 remaining**: Healthy — no action
- **1-2 remaining**: Warning in report
- **0 remaining**: Generate next batch

### Investigation Probes

When generating tasks, the Coach probes:

1. **API health**: `curl /api/v1/health`
2. **Proxy health**: `curl frontend→API route`
3. **Key endpoints**: courses, variants, health (200 vs 500)
4. **Database**: check seed data in key tables
5. **Deploy log**: check for rollbacks
6. **Browser**: load key pages, check console errors

### Scoring Formula

```
priority_score = blocking_weight × confidence
```

| Factor | Weight |
|--------|--------|
| Blocks ALL user work | 3.0× |
| User-facing breakage | 2.0× |
| Infrastructure gap | 1.5× |
| Polish | 1.0× |

Top 3-5 scored gaps become the next batch of tasks.

## Skills Integration

Each project declares skills in its `AGENTS.md ## Skills` section. The cron job loads these at start. Project skills are additive to the role skills (player-agent, coach-agent).

| Skill Layer | Where | Example |
|-------------|-------|---------|
| Role (always) | Cron job config | `player-agent`, `coach-agent` |
| Project (per-repo) | AGENTS.md `## Skills` | `subagent-driven-development` |
| Task (per-task) | Per-task metadata in AGENTS.md | (optional override) |
