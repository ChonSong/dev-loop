# Cron Job Setup

Four cron jobs drive the autonomous dev system. Three are LLM-driven agents; one is a script-only pipeline.

## Player Cron

Runs every 30 minutes, implements one task from the backlog.

| Field | Value |
|-------|-------|
| **Job ID** | `b4f35d68ede1` |
| **Name** | `player-development-loop` |
| **Schedule** | `*/30 * * * *` (every 30min at :00) |
| **Skills** | `["player-agent"]` |
| **Model** | `deepseek-v4-flash` via `opencode-go` |
| **Toolsets** | `["terminal", "file", "web"]` |
| **Deliver** | `local` |

```bash
cronjob(action='create',
  name='player-development-loop',
  schedule='*/30 * * * *',
  prompt='Execute the player-agent role. Read master checkpoint, find the next pending task, implement it, test, commit, and push.',
  skills=['player-agent'],
  model={'provider': 'opencode-go', 'model': 'deepseek-v4-flash'},
  enabled_toolsets=['terminal','file','web'],
  deliver='local')
```

## Coach Cron

Runs 5 minutes after the Player. Reviews the last commit, runs live site QA, probes for spec gaps (using delegation for parallel probes), checks backlog health, and generates the next batch of tasks.

| Field | Value |
|-------|-------|
| **Job ID** | `5e1bba516d87` |
| **Name** | `coach-development-loop` |
| **Schedule** | `5,35 * * * *` (every 30min at :05) |
| **Skills** | `["coach-agent"]` |
| **Model** | `deepseek-v4-flash` via `opencode-go` (reliability > model separation) |
| **Toolsets** | `["terminal", "file", "web", "browser", "session_search", "delegation"]` |
| **Deliver** | `local` |

```bash
cronjob(action='create',
  name='coach-development-loop',
  schedule='5,35 * * * *',
  prompt='Execute the coach-agent role. Review the last player commit, verify against AGENTS.md criteria, run live site QA, and output DECISION: APPROVE/FIX/REVERT. Then check backlog health, probe for spec gaps, and generate tasks if needed.',
  skills=['coach-agent'],
  model={'provider': 'opencode-go', 'model': 'deepseek-v4-flash'},
  enabled_toolsets=['terminal','file','web','browser','session_search','delegation'],
  deliver='local')
```

### Why delegation is included

The Coach runs 11 independent probes per tick (6 spec gap checks + 5 external discovery sources). Without delegation these run sequentially, consuming ~330s of the time budget. With delegation, up to 3 concurrent subagents run independent probes, cutting wall-clock to ~90s.

Subagents are leaf agents (cannot re-delegate) with toolset-limited scope tailored to each probe.

## Self-Improvement Engine (SIE) Cron

Runs every 48 hours. Scans for coverage blind spots, processes `.learnings/` entries, and authors skills.

| Field | Value |
|-------|-------|
| **Job ID** | `83e9c3a48cff` |
| **Name** | `Self-Improvement Engine` |
| **Schedule** | `0 */48 * * *` (every 48 hours) |
| **Workdir** | `/home/sc/repos/hermes-sync` |
| **Model** | Inherits from default |
| **Toolsets** | `["terminal", "file", "delegation"]` |
| **Deliver** | `local` |

```bash
cronjob(action='create',
  name='Self-Improvement Engine',
  schedule='0 */48 * * *',
  workdir='/home/sc/repos/hermes-sync',
  prompt='[Phase 0: Coverage blind-spot scan... then run Python pipeline]',
  enabled_toolsets=['terminal','file','delegation'],
  deliver='local')
```

### Why delegation is included

Phase 0 reads the master checkpoint and audits each project for coverage gaps. With multiple projects, delegation spawns one subagent per project for parallel audit, then collates results and seeds `.learnings/` entries.

## Memory Curation Cron *(not part of dev loop)*

Daily audit of all projects. Flags stalled tasks, evaluates coach quality.

| Field | Value |
|-------|-------|
| **Job ID** | `0175050d9c29` |
| **Name** | `Memory Curation` |
| **Schedule** | `0 16 * * *` (daily at 4pm) |
| **Toolsets** | `["search", "file", "terminal"]` |
| **Deliver** | `local` |

Does not use delegation — its work is sequential (search sessions → write memory).

## Cron Management Notes

- Use `cronjob(action='list')` to see all jobs, their models, and statuses
- Use `cronjob(action='update', job_id='...')` to change model, toolsets, schedule, or delivery
- Use `cronjob(action='pause', job_id='...')` to pause without deleting

### Timeout Model

Cron jobs use an **inactivity-based timeout** (not a hard wall clock):
- **Default**: 600s (10 min) of inactivity
- Job runs indefinitely as long as it's making tool calls or receiving stream tokens
- Override via `HERMES_CRON_TIMEOUT` env var (`0` = unlimited)
- `delegation` is NOT in the protected list — available when included in `enabled_toolsets`

### Protected Toolsets (always disabled in cron context)

These three toolsets are hard-blocked in every cron run regardless of `enabled_toolsets`:

- `cronjob` — prevent recursive job scheduling
- `messaging` — requires an active gateway session
- `clarify` — blocking; cron runs have no user to answer

### Model Reliability Strategy

| Tier | Use Case | Model |
|------|----------|-------|
| **Implementation** | Player coding, mechanical tasks | `deepseek-v4-flash` (free via opencode-go) |
| **Review + research** | Coach review, gap detection, backlog gen | `deepseek-v4-flash` (free via opencode-go) |
| **Meta-improvement** | SIE scanning, skill authoring | Inherits default |
| **No LLM** | Script-only watchdogs, log rotation, DB compaction | `no_agent: true` |

Key rule: **reliability > model separation**. A Coach that errors from rate limits is worse than a Coach sharing the Player's model. If a cron job shows `last_status: error` with `HTTP 429`, switch to a reliable free-tier provider.
