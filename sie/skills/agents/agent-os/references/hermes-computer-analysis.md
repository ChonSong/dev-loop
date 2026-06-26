# Hermes-Computer Analysis (2026-05-10)

## Vision
"One website to rule them all" — combine agent-os + hermes-workspace + hermes-computer + project management into a single modular platform.

## Key Decision: Modular Platform (Option C)
Core shell (auth, sidebar, theming, notifications) + feature packs that can be toggled. Agent-os is the foundation. Computer-use is a feature pack. Project management is another. Without modularity, you'll have a 50MB SPA bundle and nobody will use half of it.

## Architecture Decisions

| Decision | Recommendation | Rationale |
|----------|----------------|-----------|
| Backend language | Keep Express.js | Already has 30+ working endpoints. Rewrite in Go = months for marginal benefit. Use Go for sandbox/PTY only if needed. |
| Frontend framework | Stay with React + Vite | 22 pages, 11 themes, 36 migrated components already exist. SvelteKit switch = rebuild from scratch. |
| Computer-use sandbox | Docker exec + screenshots (MVP) | Working in days, not weeks. Add mouse/keyboard/H.265 later. |
| Project management | Minimal tasks first (CRUD + status) | No Gantt, no Kanban, no time tracking initially. Just: tasks, status, assignee. |
| Multi-agent orchestration | Simple orchestrator (agent spawning) | One agent spawns sub-agents, waits for results, combines outputs. No durable execution yet. |
| Database | Single PostgreSQL | Add tables for tasks, projects, kanban, time entries. No second database unless proven need. |
| Computer-use UI | New `/computer` page | Left: desktop viewer. Right: existing ChatPanel. Bottom: controls (interrupt, pause, resume). |
| Deployment | Keep Docker compose | Each sandbox = container with resource limits. Use agent-os_agent-net. No K8s yet. |

## Computer-Use Repos Analysis

### trycua/cua (15,833 stars)
**Most useful.** Sandbox SDK interface (`Sandbox.shell`, `Sandbox.screenshot`, `Sandbox.mouse`, `Sandbox.keyboard`) is the blueprint for PTY supervisor. Port to Go. Benchmark suite validates interrupt latency.

### bytebot-ai/bytebot (11,003 stars)
**Strong conceptual reference.** Takeover Mode is closest existing implementation to interrupt model. LiteLLM integration for 100+ providers. But stack is antithesis of "lean" (NestJS + Next.js + Ubuntu XFCE).

### roguedev-ai/kasm-mcp-server-v2 (4 stars)
**Partially useful.** 21-tool taxonomy maps well to PTY supervisor needs. But MCP dependency is explicitly rejected. Steal the tool taxonomy, drop the MCP wrapper.

### coder/coder-desktop-linux (6 stars)
**Not useful directly.** C#/.NET + AGPL-3.0. Wrong language, wrong license, too narrow. VPN connectivity concept is interesting.

## Features List Repo

`github.com/ChonSong/features-list` contains:
- 4 architecture diagrams (HTML/SVG)
- 5 screenshots from hermes-workspace
- Complete feature catalog: agent-os + hermes-workspace + repo-transmute v2
- 100+ future ideas across 18 categories

## Priority Order

1. **Integrate the 36 migrated components** — finish what's started
2. **Add RAG support** — document loaders, text splitters, vector store
3. **Build simple orchestrator** — agent spawning + result combining
4. **Minimal task system** — CRUD + status, no Gantt/Kanban
5. **Workflow chaining UI** — let users build multi-step agent pipelines
6. **Computer-use MVP** — Docker exec + screenshots, `/computer` page
