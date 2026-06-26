# hermes-workspace → agent-os Fusion Plan

**Date:** 2026-05-09  
**hermes-workspace:** github.com/outsourc-e/hermes-workspace (3,412 stars)  
**Stack:** React 19 + TanStack Start + Vite 7 + Tailwind CSS 4 + Zustand + xterm.js + Monaco  
**agent-os:** github.com/ChonSong/agent-os  
**Stack:** Express + Socket.IO + Dockerode + PG + React 19 + Vite + Tailwind v4 + Python nanobot

## Architecture Difference

hermes-workspace is a **client SPA** that talks to vanilla Hermes Agent's gateway API (port 8642) and dashboard API (port 9119). It has its own TanStack Start backend that proxies to those endpoints.

agent-os **is** the agent + dashboard in one Docker image. It has an Express backend (port 3001/9120) that directly manages Docker, PG, nanobot, and serves the React SPA.

**Fusion =** port hermes-workspace's superior UI/UX and features into agent-os's existing Express+React architecture.

## Features hermes-workspace has that agent-os lacks

| Feature | hermes-workspace | agent-os | Migration Effort |
|---|---|---|---|
| **Chat** | Full SSE, tool calls, multi-session, fork, slash cmds, voice | ChatPanel only, `/chat` broken (xterm/PTY) | Medium — SSE logic rewiring |
| **Terminal** | Full PTY via xterm.js, persistent sessions | None | Medium — needs new Express PTY endpoint |
| **Memory Browser** | Browse/search/edit `~/.hermes/` | None | Medium — needs Express memory endpoints |
| **MCP Page** | Catalog + marketplace + server config | None | Medium — needs Express MCP proxy |
| **Inspector Panel** | Session activity sidebar | None | Easy — UI only, wire to existing APIs |
| **Agent View** | Live agent panel, queue, history, usage | None | Easy — UI only |
| **Swarm Mode** | tmux-backed multi-agent orchestration | None | Hard — needs new backend services |
| **Operations** | Multi-agent registry (pause/steer/kill) | None | Hard — needs new backend services |
| **Conductor** | Mission dispatch UI | None | Hard — needs new backend services |
| **Themes** | 8 themes (Matrix/Official/Classic/Slate/Nous × dark+light) | Warm bento only | Easy — CSS vars transplant |
| **PWA** | Installable app, Tailscale | None | Easy — manifest + service worker |
| **Auth** | Middleware on all routes | None | Medium — needs Express middleware |
| **Files** | Monaco editor, upload, glob filter | Basic text edit | Medium — add Monaco + upload |

## Recommended Migration Phases

### Phase 1 — Visual Design Transplant (1-2 days)
- Copy hermes-workspace's theme system (`src/styles.css` ~800 lines of CSS vars for 8 themes × 2 modes)
- Copy component library (`src/components/` — 80+ components: chat, inspector, memory, skills, terminal, auth, onboarding, etc.)
- Copy routing structure (TanStack Router → React Router adaptation)
- Wire components to existing agent-os API endpoints where they already match (sessions, cron, profiles, skills, files, docker)

### Phase 2 — Backend Gap Fill (1-2 days)
- Add Express PTY endpoint for terminal (`/api/terminal-stream` + `/api/terminal-input`)
- Add Express memory browse/search/write endpoints
- Add Express MCP catalog proxy endpoint
- Add Express auth middleware
- Add Monaco editor + file upload to FileExplorerPage

### Phase 3 — Agent-Native Features (2-3 days)
- Build Swarm Mode as agent-os native feature (Docker-based multi-agent, not tmux-based)
- Build Operations panel for agent-os's Docker containers + nanobot agents
- Build Conductor for mission dispatch using agent-os's existing nanobot architecture

**Key principle:** Build Swarm/Conductor/Operations around agent-os's actual architecture (Dockerode, nanobot, PG), NOT by porting hermes-workspace versions which assume tmux + Hermes infrastructure.

## Critical Decision: Backend Strategy

**Keep agent-os Express backend.** Do not replace with TanStack Start.

Reasoning:
1. agent-os backend is already comprehensive (75 routes, Dockerode, PG, Socket.IO, cron, profiles, skills)
2. hermes-workspace backend is designed to proxy to Hermes Agent gateway — agent-os IS the agent
3. Keeping one backend avoids duplicating Docker/PG/Socket.IO logic
4. Express API is stable and deployed; ripping it out for TanStack SSR is high risk
5. hermes-workspace's frontend components can be extracted as pure React (Zustand + API calls) without TanStack Start dependency

## What NOT to Do

- **Do NOT use repo-transmute** — it's a 58-line stub returning empty results
- **Do NOT port hermes-workspace's TanStack Start backend** — unnecessary complexity
- **Do NOT blindly copy Swarm/Conductor** — they depend on tmux-backed Hermes infrastructure agent-os doesn't have
- **Do NOT merge into TanStack SSR** — agent-os is already Docker-deployed with Express
