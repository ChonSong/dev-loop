# Architecture

## Overview

The dev loop implements a **dialectical autocoding** pattern — two agents with different roles, different models, iterating on the same work. The Player implements, the Coach adversarially reviews.

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
     │  Player Cron   │  │  Coach Cron     │  │  Memory      │
     │  (every :00)   │  │  (every :05)    │  │  Curation    │
     │                │  │                 │  │  (daily 4pm) │
     │ Flash/cheap    │  │ Stronger model  │  │              │
     │ model          │  │                 │  │              │
     └───────┬────────┘  └────────┬────────┘  └──────┬───────┘
             │                    │                    │
             ▼                    ▼                    ▼
     ┌─────────────────────────────────────────────────────┐
     │                  Per-Project Repos                    │
     │  ┌───────────────────────────────────────────────┐   │
     │  │  AGENTS.md  │  .checkpoint.json  │  src/      │   │
     │  └───────────────────────────────────────────────┘   │
     └─────────────────────────────────────────────────────┘
```

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
