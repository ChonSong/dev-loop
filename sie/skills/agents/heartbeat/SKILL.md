---
name: heartbeat
description: "Heartbeat workflow for proactive monitoring. Migrated from OpenClaw. Use when receiving heartbeat polls or for proactive background checks."
metadata:
  migrated-from: openclaw
  role: heartbeat
  owner: ChonSong
---

# Heartbeat Workflow

## Current Phase

Collection — building the code library by ingesting interesting GitHub repos.

## Phases

1. **Collection** – Build code library by ingesting interesting GitHub repos
2. **Dashboard Development** – Build dashboard variants once library has critical mass
3. **Multi-Variant Expansion** – Fork dashboards with different agent configurations

## Heartbeat Cycle

1. **Memory Review** – Scan recent memory files for new decisions
   - Primary: `/opt/data/hermes-sync/memory/MEMORY.md` (canonical, synced to GitHub)
   - Secondary: `/opt/data/memories/MEMORY.md` (may be permission-locked as root)
   - Tertiary: `memory/` under active workspace (e.g., `/opt/data/workspace/memory/`)
   - If `memory` tool is disabled (common in cron context), use `terminal` with `cat` to read files
   - Write entries to the canonical hermes-sync path; if read-only mount blocks writes, queue entries in response for next TUI session
2. **Dynamic Reconnaissance** – If queue empty, find new repos via web search
3. **Delegation** – Spawn codi to digest a target repo
4. **Curation** – Update CODE_INDEX.md with 5W1H entry

If idle, reply `HEARTBEAT_OK`.

## State File

`memory/heartbeat-state.json` tracks last check timestamps. Multiple copies exist — check `/opt/data/workspace/memory/heartbeat-state.json` first, then `/opt/data/hermes-sync/workspace/memory/heartbeat-state.json`.

## Pitfalls

- **Read-only sync mount**: `/opt/data/hermes-sync/` is mounted read-only in the container. MEMORY.md writes from cron will fail. Use `terminal` to append, or queue entries for TUI delivery.
- **Stale lock files**: `MEMORY.md.lock` and `USER.md.lock` may block concurrent writes. Safe to `rm -f` if no other process holds them.
- **Root-owned files**: Some memory files under `/opt/data/memories/` are owned by root and inaccessible. Prefer the hermes-sync copy.
- **Stale state**: heartbeat-state.json can go weeks without updates if no repos are queued. A stale timestamp + empty queue means the collection phase is stalled — flag it for Sean to decide: add repos to queue or transition to Dashboard Development phase.
- **OpenRouter 402**: If session_search or LLM calls return credit errors, note it in memory rather than retrying. The agent cannot self-heal depleted credits.
