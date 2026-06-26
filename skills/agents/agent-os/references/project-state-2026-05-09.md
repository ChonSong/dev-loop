# agent-os Project State — 2026-05-09 (end of day)

## Live Containers (host Docker)
| Container | Image | Status | Ports |
|---|---|---|---|
| `agent-os-backend` | rebuilt image w/ node fix | healthy | 3001, 1331→3001 |
| `agent-os-postgres` | `postgres:16-alpine` | healthy | 127.0.0.1:5432 |
| `agent-os-cloudflared` | `cloudflare/cloudflared:2026.3.0` | running | → backend:3001 |
| ~~`agent-os-nanobot`~~ | — | **REMOVED** | — |
| ~~`agent-os-webhook-emitter`~~ | — | **REMOVED** | — |
| `agent-os-hermes` | `nousresearch/hermes-agent:latest` | **NOT RUNNING** | port conflict 8642 |

## Repo Status
- **Latest commit**: `929ec16` ("fix: MemoryPage FileEntry types, remaining toast refs, ChatPage deps")
- **Uncommitted**: `M Dockerfile` (COPY --from=ts-build node/npm/corepack fix — critical, must commit)
- **Local state**: clean except Dockerfile

### Commit history (sessions baabd3 + 6e063d, 2026-05-09):
1. `929ec16` — fix: MemoryPage FileEntry types, remaining toast refs, ChatPage deps
2. `eb1121b` — fix: toast API in ChatPage, MCPPage, DashboardPage
3. `80807a6` — fix: restore standard turbo build
4. `32a7f54` — fix: useToast API in MemoryPage + TerminalPage
5. `85fb383` — fix: add tsc diagnostics on build failure
6. `3a684a6` — fix: jsonError → jsonErr in MCP endpoints
7. `048f0c0` — feat: Phase 1.4 — Refactor Dockerfile for Hermes replacement
8. `606c4c0` — feat: Phase 1.2-1.3 — Replace nanobot with Hermes Agent

## Architecture Changes (session baabd3)

**Nanobot → Hermes replacement completed in code:**
- `docker-compose.yml`: added `hermes` service, removed `nanobot` and `webhook-emitter`
- Backend `index.ts`: all nanobot references replaced with Hermes (`http://hermes:8642`)
- Env vars: `NANOBOT_API_URL` → `HERMES_API_URL`
- Dockerfile: removed nanobot Python install, simplified to Express backend + Go webhook-emitter only
- `COPY --from=ts-build` fix added for node binary (uncommitted)

**Hermes container fails to start** — port 8642 conflicts with host Hermes on same host. Resolution pending.

## Frontend Beautification (session 6e063d — ephemeral)

Session 6e063d applied TypeUI Bento warm cream theme:
- Background: `#FFF5E6` (warm cream)
- Cards: `#FFFBF5`
- Accent: `#FAD4C0` (peach)
- Fixed `timeAgo()` NaN bug, polished multiple pages

**These changes are container-only** — not committed to git. They will be lost on next `docker build`.

## Disk State
- Was 99-100% during session 6e063d (nearly crashed)
- Reclaimed ~30GB in session baabd3 (old images, tmp files)
- Weekly `docker system prune` cron added (Sundays 3am)
- Still around 90% — needs monitoring

## Critical Next Steps
1. **Commit Dockerfile fix** — the `COPY --from=ts-build` lines are essential for container startup
2. **Resolve Hermes port conflict** — assign different port or use network isolation
3. **Persist frontend beautification** — extract changes from running container into git source
4. **Update MASTER_PLAN.md** — reflect current state
