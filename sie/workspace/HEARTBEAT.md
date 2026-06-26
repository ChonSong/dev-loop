# Heartbeat Workflow

**Current Phase**: Collection (priority 1)
**State file**: `memory/heartbeat-state.json`

## Phases
1. **Collection** – Build the code library by ingesting interesting GitHub repos.
2. **Dashboard Development** – Once library has critical mass, start building dashboard variants.
3. **Multi‑Variant Expansion** – Fork dashboards with different agent configurations.

## Heartbeat Cycle
- **Memory Review** – Scan recent memory files for new decisions.
- **Dynamic Reconnaissance** – If queue empty, use `gh` to find new repos.
- **Delegation** – Spawn `codi` to digest a target repo.
- **Curation** – Update `CODE_INDEX.md` with 5W1H entry.

If idle, reply `HEARTBEAT_OK`.
