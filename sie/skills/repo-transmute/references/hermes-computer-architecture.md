# Hermes-Computer Architecture Reference

> How agent-os, hermes-agent, and hermes-web-computer fit together

## The Three Pillars

| Component | Role | Stack | Status |
|-----------|------|-------|--------|
| **hermes-web-computer** | Tiling AI desktop shell | Go + Svelte 5 | 70% complete |
| **hermes-agent** | AI brain (stays separate) | Python + FastAPI | 100% working |
| **agent-os** | Legacy dashboard (migration source) | React + Express | 100% working |

## Architecture Flow

```
User opens hermes-web-computer → tiling interface
  ↓
User splits tiles → Terminal, Browser, Dashboard, Voice appear
  ↓
Each tile talks to Go backend via WebSocket (JSON-RPC)
  ↓
Go backend routes to Hermes Agent for AI, Docker for sandbox, APIs for data
  ↓
Hermes uses skills, tools, memory to respond
  ↓
Responses flow back to tiles via WebSocket
```

## Current State

### hermes-web-computer (70% done)
- ✅ WebSocket multiplexer (470 lines)
- ✅ PTY supervisor with ring buffer
- ✅ Layout engine (split/mount/unmount/resize/swap/fullscreen)
- ✅ Security enforcer (YAML permissions, token-gated execution)
- ✅ Telemetry (JSONL ring buffer, async sync)
- ✅ Svelte 5 SPA (Tile, Terminal, CommandPalette, KeymapOverlay)
- ✅ Docker Compose + Caddy
- ✅ CI/CD + E2E test passing
- ❌ Hermes agent integration (TODO in tool.execute)
- ❌ LiteLLM adapter
- ❌ Fun-Audio-Chat bridge (stub)
- ❌ Monaco editor tile (stub)

### Migration Targets

| Tile | Source | Effort | Priority |
|------|--------|--------|----------|
| Terminal | Built-in | ✅ Done | v1.0 |
| Browser | bytebot (migrate) | 5 days | v1.0 |
| Dashboard | agent-os (migrate React→Svelte) | 3 days | v1.0 |
| Voice Chat | Fun-Audio-Chat (owned) | 2 days | v1.0 |
| Code Editor | Monaco.svelte (stub) | 1 day | v1.1 |
| Sandbox | cua (migrate) | 5 days | v1.1 |
| File Manager | Build from scratch | 2 days | v1.2 |

## Key Files

| Repo | Path | Purpose |
|------|------|---------|
| hermes-web-computer | `backend/ws/multiplexer.go` | JSON-RPC routing |
| hermes-web-computer | `backend/pty/supervisor.go` | PTY lifecycle |
| hermes-web-computer | `backend/layout/tree.go` | Layout engine |
| hermes-web-computer | `frontend/src/components/Tile.svelte` | Recursive tile renderer |
| hermes-web-computer | `frontend/src/components/Terminal.svelte` | xterm.js terminal |
| hermes-computer-planning | `ONE-WEBSITE.md` | Architecture analysis |
| hermes-computer-planning | `completion-plan.md` | Technical completion plan |
| hermes-computer-planning | `APPLICATION-PLAN.md` | Strategic tile migration plan |

## Vision

"one website to rule them all" — a single tiling AI desktop where:
- All agent-os pages become tiles
- Computer-use sandbox is a tile
- Voice chat is a tile
- Browser automation is a tile
- Code editing is a tile
- Everything communicates through Hermes Agent

## Planning Repo

https://github.com/ChonSong/hermes-computer-planning
- `ONE-WEBSITE.md` — Complete architecture analysis
- `completion-plan.md` — Technical completion roadmap
- `APPLICATION-PLAN.md` — Strategic tile migration plan
- `README.md` — Analysis of 4 computer-use repos
