---
name: agent-os-architecture
description: "Architecture reference for ChonSong/agent-os — the Node.js/Express/React/Postgres stack being replaced by HWC (hermes-web-computer Go backend). Read before planning any migration work. Not for new development."
tags: ["architecture", "migration", "node", "express", "react", "postgres", "nanobot", "container"]
required_environment_variables: []
required_commands: ["node", "npm", "psql", "docker"]
---

# agent-os Architecture Reference

> ⚠️ **DEPRECATED — Do not build new features here.** This repo is on the chopping block. All features must migrate to HWC's Go backend.
> This skill is for understanding the current system so nothing gets lost in migration.

## What agent-os IS

The current live production system — a Node.js/Express + React SPA with Postgres database, running nanobot (container management), Hermes agent integration, and a Cloudflare tunnel. It was HWC's predecessor for web-based AI interaction.

## Architecture Overview

```
Browser → Cloudflare Tunnel → agent-os (Node/Express) → nanobot (container) + hermes (agent)
                                      ↓
                                  Postgres (sessions, state)
```

**Ports (verify with `ss -tlnp` on host):**
| Port | Service | Notes |
|------|---------|-------|
| 3001 | agent-os Express | localhost only |
| 3113 | agent-os Express | all interfaces — frontend connects HERE |
| 5432 | PostgreSQL | agent-os DB |
| 8642 | Hermes Agent | subprocess managed by agent-os |
| 8900/8901/9120 | nanobot | container management API + workspace ports |

**Critical architectural mismatch:**
- Frontend `ws.ts:139` hardcoded: `ws://localhost:3113/ws` → connects to agent-os Express
- HWC Go backend runs on **port 3005** but receives NO frontend connections
- HWC frontend and agent-os frontend are both serving, but only agent-os is actually connected

## Key Features (must migrate to HWC)

1. **Container management** (nanobot at 8900/8901/9120) — workspaces, code execution environments
2. **Hermes agent integration** (port 8642) — the actual LLM agent backend
3. **Session/state persistence** (Postgres on 5432) — user sessions, workspace state
4. **Cloudflare tunnel** — `fe36ddb5` subdomain for remote access
5. **Real-time streaming** (SSE/WebSocket) — chat, tool results, agent updates

## Migration Priorities

1. **Container management** → HWC Docker Manager (`docker/manager.go`) — must wire nanobot's API
2. **WebSocket multiplexer** → HWC `ws/multiplexer.go` — already exists but not wired to frontend
3. **Hermes agent streaming** → HWC `agent/streamer.go` — already exists
4. **Session persistence** → HWC `session/store.go` — already exists (JSON file-based)

## What HWC Already Has (that matches agent-os)

| agent-os feature | HWC equivalent | Status |
|-----------------|-----------------|--------|
| Chat streaming | `agent/streamer.go` | ✅ exists, not wired |
| Session store | `session/store.go` | ✅ exists |
| Profile management | `profiles.svelte.ts` | 🔶 stub |
| Skills panel | `skills.svelte.ts` | 🔶 stub |
| Crons panel | `crons.svelte.ts` | 🔶 stub |
| Memory panel | `memory.svelte.ts` | 🔶 stub |
| Docker manager | `docker/manager.go` | ✅ exists |
| LLM router | `llm/router.go` | ✅ exists |
| Workspace file browser | `FileTree.svelte` | ❌ stub, not wired |
| Slash commands | — | ❌ missing |
| Onboarding wizard | — | ❌ missing |

## What HWC is Missing (from Hermes WebUI)

| Feature | Hermes WebUI | HWC status |
|---------|-------------|-----------|
| Workspace file browser + inline preview | ✅ full | ❌ stub |
| Slash commands (`/` registry) | ✅ 1302 lines | ❌ missing |
| Onboarding wizard | ✅ | ❌ missing |
| Full session projects/tags | ✅ | 🔶 partial |
| Provider/model discovery | ✅ | 🔶 partial |
| Voice input | ✅ | 🔶 partial |
| Session search | ✅ | ⚪ not started |
| File upload | ✅ | ⚪ not started |

## Inspiration Repositories (confirmed 2026-05-25)

The complete set of inspiration repos for the HWC migration/replacement:
1. `outsourc-e/hermes-workspace` — React/Electron desktop (source for features-list extraction)
2. `ChonSong/features-list` — 629 components extracted from hermes-workspace
3. `ChonSong/agent-os` — current live system (container management + nanobot)
4. `hermes-webui` — Python/vanilla JS chat UI (being replaced)
5. VoltAgent/awesome-agent-skills (~1117 skills)
6. `mattpocock/skills`, `0xNyk/awesome-hermes-agent`, `vercel-labs/skills`, `expo/skills` — skill sources

## Related

- `hermes-web-computer`: the Go/Svelte5 target architecture
- `hermes-webui`: the Python/vanilla JS chat UI also being replaced by HWC
- `repo-transmute`: for migrating components from hermes-workspace to HWC