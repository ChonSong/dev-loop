# agent-os Architecture State (updated 2026-05-09)

## Migration Status: Nanobot → Hermes (In Progress)

**Decision made: Option A — Replace nanobot container with Hermes Agent container.**

### What was done (session baabd3, commit `606c4c0`):
- Backend `index.ts`: all `nanobot` references replaced with `hermes`
  - `http://nanobot:8900` → `http://hermes:8642`
  - `NANOBOT_API_URL` → `HERMES_API_URL`
  - Comments updated: "nanobot" → "Hermes Agent"
- `docker-compose.yml`: added Hermes service (`nousresearch/hermes-agent:latest`), removed nanobot + webhook-emitter
- Dockerfile: removed nanobot Python install, added `COPY --from=ts-build` for node binary
- Entrypoint: simplified to backend-only (no nanobot service)

### What's NOT done:
1. **Hermes container won't start** — port 8642 conflicts with host Hermes. Need network isolation or alternate port.
2. **Dockerfile fix uncommitted** — the `COPY --from=ts-build` lines are on disk but not pushed
3. **Hermes config for agent-os** — Hermes needs agent-os-specific config (model, system prompt, etc.)
4. **Webhook-emitter** — removed from compose but its Go binary is still in the image. May need to re-add as sidecar or merge into backend.

### Current Running State:
```
Host Hermes (8642/9119) ← runs skills, memory, TUI, cron
    ↕
agent-os-backend (3001/1331) ← Express, proxies to hermes:8642 (but hermes container down)
    ↕
agent-os-postgres (5432)
agent-os-cloudflared → backend:3001
```

### Architecture Diagram (Target):
```
Cloudflare Tunnel
    → agent-os-backend:3001 (Express + Socket.IO)
        ├── agent-os-hermes:8642 (Hermes gateway — AI chat, tools)
        ├── agent-os-postgres:5432 (sessions, messages, cron)
        └── serves React SPA (frontend dist)
```

### Port Conflict Resolution Options:
1. Run Hermes container on internal network only (no host port binding) — backend accesses via Docker network
2. Use different host port (e.g., 8643) for docker Hermes
3. Stop host Hermes and consolidate everything into Docker
