# Memory Curation Architecture (2026-06-08)

## Three-Layer Model

| Layer | Location | Updated by | Purpose |
|-------|----------|------------|---------|
| **Raw logs** | `/workspace/memory/YYYY-MM-DD.md` | Agent at session end | Structured daily record of what happened |
| **Distilled** | `/workspace/MEMORY.md` | Daily cron job (16:00 UTC) | Curated long-term facts, 50 lines max |
| **Injected** | Agent `memory` tool | Manually, sparingly | Critical paths/ports only, ≤2,200 chars |

## Canonical Paths (DO NOT USE OLD ONES)

| Old (dead/stale) | New (canonical) |
|-------------------|-----------------|
| `/opt/data/hermes-sync/memory/MEMORY.md` | `/workspace/MEMORY.md` |
| `/opt/data/home/.hermes/memories/MEMORY.md` | `/workspace/MEMORY.md` |
| `/opt/data/hermes-web-computer/` | `/home/hermeswebui/.hermes/hermes-web-computer` |

## Curation Cron Job Pattern

```
Job: Memory Curation
Schedule: 0 16 * * * (daily at 16:00 UTC)
deliver: origin (visible to user)
Model: current default

Prompt structure:
1. session_search for recent activity (6-7 queries in parallel)
2. Read recent daily logs from /workspace/memory/
3. Read current /workspace/MEMORY.md for comparison
4. Identify changes, staleness, gaps
5. OVERWRITE /workspace/MEMORY.md (50 lines max, declarative facts)
6. Create today's daily log if missing
7. Output summary of what changed
```

## Memory Tool (`memory` tool) Usage

- Hard limit: 2,200 chars total across all entries
- Use for: critical environment facts, auth methods, port numbers, paths
- Do NOT duplicate what's in /workspace/MEMORY.md
- `replace` and `remove` use exact substring matching — match on the SHORT KEY from the injected context, not the full entry text
- When replacing, make the replacement DENSER to free up space
- If writes fail due to limit, first prune stale entries, then retry

## Daily Logging Convention

Write `/workspace/memory/YYYY-MM-DD.md` when:
- 5+ tool calls in a session
- Project milestone reached or phase completed
- Non-trivial error overcome
- Infrastructure change or config update

Format:
```
# YYYY-MM-DD — Daily Notes
## [Topic]
### Actions / Decisions
### Files Changed
### Pending
```

Skip for trivial Q&A sessions. Write BEFORE session ends — don't rely on curation to reconstruct.
