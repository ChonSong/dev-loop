# Hermes-Computer Planning Analysis (2026-05-10)

## Repos Analyzed

| Repo | Stars | Language | License | Relevance |
|------|-------|----------|---------|-----------|
| coder/coder-desktop-linux | 4 | C# (.NET/Avalonia) | AGPL-3.0 | Remote workspace connectivity |
| roguedev-ai/kasm-mcp-server-v2 | 3 | Python | MIT | Kasm workspace MCP control |
| bytebot-ai/bytebot | 11,003 | TypeScript | Apache-2.0 | Full desktop AI agent |
| trycua/cua | 15,833 | Python/Swift/TS | MIT | Cross-OS computer-use infra |

## Key Takeaways

### What Works (validated by repos)
1. **Containerized desktop environments** — Bytebot and Cua prove this model works
2. **Agent-in-loop with human takeover** — Bytebot's Takeover Mode validates the concept
3. **Cross-platform sandbox abstraction** — Cua's unified API is the right interface
4. **Tool taxonomy for workspace control** — Kasm's 21 tools map well to agent needs
5. **Self-hosted, privacy-first** — All four repos validate market need

### What to Avoid
- Full Ubuntu XFCE desktop (too heavy — use minimal containers)
- NestJS + Next.js stack (Node.js overhead)
- AGPL-3.0 license (viral, incompatible with commercial reuse)
- C#/.NET stack (wrong language/ecosystem)
- MCP-only dependency (adds protocol tax)
- 207MB monorepo (be modular)

### What to Borrow
- **trycua/cua**: Sandbox SDK interface (shell, screenshot, mouse, keyboard) — port to Go
- **trycua/cua**: Benchmark suite for interrupt latency validation
- **trycua/cua**: H.265 streaming pattern for efficient window streaming
- **bytebot**: Takeover Mode UX pattern for human-in-the-loop
- **bytebot**: LiteLLM integration for 100+ provider support
- **kasm-mcp-server-v2**: 21-tool taxonomy as native Go handlers

## hermes-web-computer Spec

Alternative architecture at `/opt/data/hermes-web-computer`:
- **Backend**: Go (`CGO_ENABLED=0 go build`)
- **Frontend**: SvelteKit + Tailwind
- **Infra**: Docker Compose with 4 services (agent-os, hermes, fun-audio, caddy)
- **Reverse proxy**: Caddy with internal TLS
- **Audio**: Fun-audio-chat subprocess with WebSocket
- **State**: SQLite + JSONL telemetry
- **License**: MIT

### docker-compose.yml
```yaml
services:
  agent-os:
    build: ../backend
    ports: ["3001:3001"]
    networks: [agent-net]
    volumes:
      - ../state:/agent/.state
      - ../telemetry:/agent/.telemetry
    environment:
      - LOG_LEVEL=info
      - FUN_AUDIO_WS=ws://fun-audio:11235/api/chat
      - TELEMETRY_ENDPOINT=${TELEMETRY_ENDPOINT:-}
    depends_on: [fun-audio]

  hermes:
    image: nousresearch/hermes-agent:latest
    network_mode: host
    volumes:
      - /host/project:/host/project:ro
      - ../state:/opt/data

  fun-audio:
    build: ../bridge
    network_mode: host
    volumes: ["../state:/opt/data"]
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  caddy:
    image: caddy:latest
    ports: ["80:80", "443:443"]
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - ../frontend/dist:/srv/frontend
    networks: [agent-net]
```

## Decision Points

### Q1: One website to rule them all?
**Recommendation**: Modular platform with core shell + feature packs. Agent-os is the foundation. Computer-use is a feature pack. Project management is another. Without modularity, you'll have a 50MB SPA bundle and nobody will use half of it.

### Q2: Backend language?
**Recommendation**: Keep Express.js. Agent-os already has 30+ working endpoints. Rewrite in Go would take months for marginal benefit. Use Go for sandbox/PTY only if needed.

### Q3: Frontend framework?
**Recommendation**: Stay with React + Vite. Already have 22 pages, 11 themes, 36 migrated components. SvelteKit switch means rebuilding everything.

### Q4: Computer-use sandbox?
**Recommendation**: Start with Docker exec + screenshots via `scrot` or `import`. Working MVP in days. Build full sandbox with mouse/keyboard/H.265 later.

### Q5: 100+ roadmap features?
**Recommendation**: Build in phases. Phase 1: minimal tasks + Kanban + wikis. Phase 2: Gantt + time tracking + custom widgets. Phase 3: full PM + invoicing + BIM.

### Q6: Database strategy?
**Recommendation**: Keep PostgreSQL as single database. Add tables for tasks, projects, kanban, time entries. Don't introduce second database unless proven need.

### Q7: Computer-use UI integration?
**Recommendation**: New `/computer` page with desktop viewer (left) + existing chat panel (right) + bottom control bar. Reuses ChatPanel, Sidebar, StatusBar.

### Q8: Deployment model?
**Recommendation**: Keep Docker compose. Each sandbox session spins up container with resource limits. Use existing agent-os_agent-net.
