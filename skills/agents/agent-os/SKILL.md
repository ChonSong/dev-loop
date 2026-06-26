---
name: agent-os
description: "Build, deploy, debug ChonSong/agent-os monorepo. Unified Docker image, Express backend, React SPA (22 pages), Hermes Agent on host via host.docker.internal. GitHub: ChonSong/agent-os, main branch. CI: SSH auto-deploy (DEPLOY_KEY + DEPLOY_HOST secrets set by user). Known issue: cloudflared tunnel uses wrong hostname."
---

# agent-os Monorepo Operations

## Repo & Access

- **GitHub**: `github.com/ChonSong/agent-os` (branch: `main`)
- **Host working dir**: `/home/sean/.hermes/agent-os` — docker-compose.yml, Dockerfile, configs
- **Local working dir**: `/opt/data/agent-os` (hermes container, git-synced clone)
- **Dockerfile on host**: `/home/sean/.hermes/hermes-sync/projects/agent-os/Dockerfile`
- **Image**: `ghcr.io/chonsong/agent-os:latest`
- **Network**: `agent-os_agent-net`
- **SSH key (container→host)**: `/opt/data/container_key`
- **SSH**: `ssh -i /opt/data/container_key -o StrictHostKeyChecking=no sean@localhost <cmd>`

## Architecture — Hermes Agent Powers agent-os (2026-05-09)

**Nanobot removed.** Backend proxies to the host's Hermes Agent via `host.docker.internal:8642`. The Hermes Agent runs on the host directly (not in docker-compose) and handles all AI chat, models, skills, memory, cron.

| Component | Location | Port | Role |
|-----------|----------|------|------|
| Hermes Agent (host) | Docker container `hermes` (hermes-sync:latest, network_mode: host) | 8642/9119 | AI engine — chat, skills, memory, TUI, cron |
| Backend | Docker (`agent-os-backend`) | 3001, 1331 | Express + Socket.IO + Dockerode, proxies to Hermes |
| PostgreSQL | Docker (`agent-os-postgres`) | 5432 | Sessions, events, cron, profiles, skills |

- Backend env: `HERMES_API_URL=http://host.docker.internal:8642`
- Backend uses `extra_hosts: ["host.docker.internal:host-gateway"]` for host access
- docker-compose.yml has NO hermes service — uses host's existing Hermes

## Container Layout (4 compose services + host Hermes)

| Container | Image | Ports | Status |
|-----------|-------|-------|--------|
| `agent-os-backend` | ghcr.io/chonsong/agent-os:latest | 3001, 1331→3001 | ✅ Healthy |
| `agent-os-postgres` | postgres:16-alpine | 5432 | ✅ Healthy |
| `agent-os-cloudflared` | cloudflared:2026.3.0 | — | ✅ Running |
| `agent-os-webhook-emitter` | ghcr.io/chonsong/agent-os:latest | — | ✅ Healthy |
| `hermes` (host) | hermes-sync:latest | 8642, 9119 | ✅ Healthy (network_mode: host) |
| ~~`agent-os-hermes`~~ | ~~nousresearch/hermes-agent~~ | ~~8642~~ | **REMOVED** — port conflict resolved by using host Hermes |
| ~~`agent-os-nanobot`~~ | ~~unified image~~ | ~~8900~~ | **REMOVED** in commit `606c4c0` |

## Frontend Pages (22)

**Status:** All 22 pages exist and serve correctly. Pages were built from scratch during agent-os development, NOT ported from hermes-workspace. The hermes-workspace frontend has NOT been migrated — its design, components, and themes remain separate.

- New pages: `/dashboard`, `/terminal`, `/memory`, `/mcp`, `/chat` (SSE)
- Theme system: `ThemeContext.tsx` defines 11 theme names but only bento CSS is active
- CSS: Hardcoded warm bento design in `index.css` (from beautification session 6e063d)
- hermes-workspace visual design: NOT applied — pages have their own styling
- See `references/hermes-workspace-migration-status.md` for full gap analysis

**v2 Migration Engine:** repo-transmute v2 now supports vision-driven migration. Use it to port hermes-workspace → agent-os with automated screenshot verification. Run `v2 ingest --local /path/to/hermes-workspace` to extract the blueprint, then `v2 migrate` to generate migrated components.

**Migrated Components (36):** repo-transmute v2 extracted 629 components from hermes-workspace and migrated 36 to agent-os format (768KB total) in `/opt/data/repo-transmute-v2/data/migrated/`. Key migrated files: chat-screen (84K), chat-composer (115K), message-item (94K), dashboard-screen (39K), providers-screen (57K), mcp-screen (17K), operations-screen (12K), command (13K), dialog (4.3K), switch (3.3K). See `references/migration-results-2026-05.md` for the full catalog.

**Features List Repo:** `github.com/ChonSong/features-list` contains a complete feature catalog of hermes-workspace with 100+ components categorized across Chat, Dashboard, MCP, Settings, Agents, and UI.

## Backend Image Build & Recovery

The unified Docker image uses **`node:22-slim`** as the runtime base — it includes Node.js v22.22.2 at `/usr/local/bin/node` by default. No manual copying of the node binary needed.

**Old approach (pre-2026-05-10, DEPRECATED):** Previously used `debian:13-slim` + `COPY --from=ts-build /usr/local/bin/node`. This was fragile because the node:22 base image would occasionally change layout, breaking the copy. The node:22-slim runtime base eliminates this entirely.

**If you see `/usr/local/bin/entrypoint.sh: exec: node: not found`:**
1. Verify the Dockerfile runtime stage starts with `FROM node:22-slim` (not `debian:13-slim`)
2. Rebuild with **`--no-cache`**: `docker build --no-cache -t ghcr.io/chonsong/agent-os:latest .`
3. Verify: `docker run --rm --entrypoint sh ghcr.io/chonsong/agent-os:latest -c 'node --version'` should return `v22.x`

**Docker CLI installation:** Installed from official static binary tarball in the Dockerfile (avoids apt package naming issues across Debian versions).

**If you see `apt-get install docker-cli: package not found`:** The Debian package name varies. Use the static binary approach:
```dockerfile
RUN curl -fsSL https://download.docker.com/linux/static/stable/x86_64/docker-27.5.1.tgz | \
    tar xz --strip-components=1 -C /usr/local/bin docker/docker
```

**Docker compose is NOT available** inside the hermes container — neither `docker compose` nor `docker-compose`. Use `docker run` directly.

**Debugging slow builds:** `docker build --no-cache` takes 5-8 minutes. If you're monitoring via SSH redirect (`> /tmp/build.log`), you'll see no output until completion. Use `--progress=plain` to stream build steps in real time. The first 2 minutes are base image pulls (node:22, golang, debian:13-slim), then 2-3 minutes for `npm install` and `turbo build`.

**TypeScript baseUrl deprecation (TS 6.x):** The `baseUrl` compiler option is deprecated in TS 6.x. **Do NOT remove `baseUrl`** — doing so breaks `paths` resolution and causes "Cannot find module" errors for all `@/` imports. The correct fix is to keep `"baseUrl": "src"` with `"paths": { "@/*": ["./*"] }` and add `"ignoreDeprecations": "6.0"` to silence the warning. Removing baseUrl requires adjusting ALL path mappings to include the `src/` prefix (e.g., `"@/*": ["./src/*"]`) which is error-prone and unnecessary until TS 7.0.

**v2 Migration Engine:** repo-transmute v2 (at `/opt/data/repo-transmute-v2`) has 36 hermes-workspace components migrated to agent-os format in `data/migrated/`. These components have dependency issues (missing recharts, motion/react, internal hooks/utils stubs) and cannot be directly dropped into the frontend. Integration requires:
1. Installing missing npm packages (recharts, motion)
2. Creating stub files for missing internal modules (hooks, utils, types)
3. Verifying no remaining `@tanstack`, `@hugeicons`, or `@base-ui` imports
4. Running `npx tsc --noEmit` to confirm compilation before building

**Image ≠ Running:** Building a new image doesn't update running containers. Must explicitly stop/rm/run. Check `docker inspect agent-os-backend --format '{{.Created}}'` — if it predates your latest commit, the container is running old code.

## Deploy

### CI Auto-Deploy (SSH-based)

The CI workflow (`agent-os.yml`) has an SSH deploy step that pulls the new image and recreates containers. It requires two GitHub repo secrets:

- **`DEPLOY_KEY`** — contents of `/home/sean/.ssh/id_ed25519_ci_deploy` (private key, already in host's `authorized_keys`)
- **`DEPLOY_HOST`** — host public IP or hostname

If secrets aren't set, the deploy step prints a warning and exits 0 (no failure).

### Manual Deploy

`docker compose up -d` can hang on the host (pulling/dependency wait). Prefer `docker run` directly:

```bash
# 1. Build (always use --no-cache — cached layers may exclude node binary)
ssh ... "cd /home/sean/.hermes/agent-os && docker build --no-cache -t ghcr.io/chonsong/agent-os:latest ."

# 2. Verify node binary exists in new image
docker run --rm --entrypoint sh ghcr.io/chonsong/agent-os:latest -c '/usr/local/bin/node --version'

# 3. Populate frontend-dist volume from image (prevents empty override)
docker run --rm -v /home/sean/.hermes/agent-os-patched/frontend-dist:/out --entrypoint sh ghcr.io/chonsong/agent-os:latest -c 'cp -a /app/apps/dashboard/frontend/dist/. /out/'

# 4. Recreate backend
docker stop agent-os-backend && docker rm agent-os-backend
docker run -d \
  --name agent-os-backend --restart unless-stopped --memory 1g \
  --network agent-os_agent-net --network-alias backend \
  --add-host host.docker.internal:host-gateway \
  -p 127.0.0.1:3001:3001 -p 127.0.0.1:1331:3001 \
  -e NODE_ENV=production -e PORT=3001 \
  -e "DATABASE_URL=postgresql://agentos:agentos_secure_pg_pass_2026@postgres:5432/agentos" \
  -e "HERMES_API_URL=http://host.docker.internal:8642" \
  -v /var/run/docker.sock:/var/run/docker.sock:rw \
  -v /home/sean/.hermes/agent-os:/opt/agent-os:ro \
  -v /home/sean/.nanobot:/root/.nanobot:rw \
  -v /opt/data:/opt/data:rw \
  -v /home/sean:/home/sean:rw \
  -v /home/sean/.hermes/agent-os-patched/frontend-dist:/app/apps/dashboard/frontend/dist:ro \
  --health-cmd "curl -sf http://localhost:3001/api/db/health" \
  --health-interval 15s --health-timeout 5s --health-retries 3 --health-start-period 15s \
  ghcr.io/chonsong/agent-os:latest backend

# 5. Recreate webhook-emitter
docker stop agent-os-webhook-emitter && docker rm agent-os-webhook-emitter
docker run -d \
  --name agent-os-webhook-emitter --restart unless-stopped --memory 256m \
  --network agent-os_agent-net \
  --health-cmd "curl -sf http://agent-os-backend:3001/api/db/health" \
  --health-interval 30s --health-timeout 5s --health-retries 3 --health-start-period 10s \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  ghcr.io/chonsong/agent-os:latest \
  webhook-emitter run --webhook-url http://agent-os-backend:3001/api/webhooks/casaos --poll-interval 10 --filter agent-os-
```

No docker-compose CLI in container — use `docker run`.

## Known Issues

1. **Disk ~90% full** — reclaimed ~30GB in session baabd3, weekly prune cron added, but still tight
2. **Cloudflared tunnel broken** — tunnel config points to `backend:3001` (docker-compose service name) but containers are launched via `docker run` with name `agent-os-backend`. **Fix:** Add `--network-alias backend` to the backend's `docker run` command OR update the tunnel token to use `agent-os-backend:3001`. See `references/cloudflared-tunnel-fix.md`.
3. **OAuth endpoints are stubs** — All 6 OAuth endpoints return placeholder data
4. **Gateway/action endpoints are stubs** — `POST /api/gateway/restart`, `POST /api/hermes/update`, `GET /api/actions/:name/status` return hardcoded responses
5. **AppStorePage has no backend** — Plugin store UI exists but backend plugin system is rudimentary

## Working Style

- **Don't ask, just do.** User prefers autonomous execution — gather context, fix, push, deploy without asking permission at each step. Present the plan once (or just the summary) and execute.
- **Push frequently.** User may be interrupted unexpectedly. Commit+push after every logical unit of work, not at the end.
- **Verify after deploy.** After rebuilding the image or recreating containers, always verify: `docker ps` for health, `curl` the API, and confirm the frontend serves. The container creation timestamp tells you if it's running old code.
- **Image ≠ Running.** Building a new image doesn't update running containers. Must explicitly stop/rm/run or the old image keeps serving. Check `docker inspect agent-os-backend --format '{{.Created}}'` — if it predates your latest commit, the container is running old code.

## Pitfalls

- **SSH key path** — container→host key is at `/opt/data/container_key`. Alternative key exists at `/opt/data/home/.ssh/id_ed25519` but requires `chmod 600` before use. If SSH fails with "Permission denied", check key permissions first.
- **Git push to `main`** (not master)
- **nanobot config** — `/home/sean/.nanobot/config.json` — **DEPRECATED**, nanobot removed. Backend now targets Hermes.
- **Hermes networking** — Backend uses `host.docker.internal:8642` to reach host Hermes. No hermes service in docker-compose.
- **`docker compose up -d` hangs on host** — when recreating containers via SSH, `docker compose up -d` can hang indefinitely (waiting on image pull or dependency health). Use `docker stop/rm/run` directly instead.
- **Build cache trap** — `docker build` caches runtime stage layers. If the Dockerfile was recently patched (e.g., adding node binary COPY), cached layers may not include the fix. Always use `docker build --no-cache` for agent-os builds.
- **Volume mount gotcha** — docker-compose mounts `/home/sean/.hermes/agent-os-patched/frontend-dist:/app/apps/dashboard/frontend/dist:ro`. If host dir missing/empty, Docker creates empty dir, overwriting baked-in frontend. Fix: `docker run --rm -v /home/sean/.hermes/agent-os-patched/frontend-dist:/out --entrypoint sh ghcr.io/chonsong/agent-os:latest -c 'cp -a /app/apps/dashboard/frontend/dist/. /out/'`
- **Container name resolution** — In `docker compose`, services resolve by service name (e.g., `backend`). With `docker run`, they resolve by container name (e.g., `agent-os-backend`). Health checks and internal URLs must use the right name for the launch method. The webhook-emitter health check uses `agent-os-backend:3001` (not `backend:3001`) because it's launched via `docker run`. **The cloudflared tunnel config still uses `backend:3001` which is WRONG** — it needs `agent-os-backend:3001` or a network alias. See Known Issues.
- **`execute_code` with `time.sleep()` is unreliable** — the 300s execution timeout means any `time.sleep(N)` where N > ~240 risks the entire script being killed before reaching subsequent code. Use `terminal` tool for health checks with explicit short timeouts instead.
- **GHCR push from host** — `docker push ghcr.io/chonsong/agent-os:latest` works from host without explicit `docker login` if the credential helper is configured via git-credentials store
- **TypeScript baseUrl deprecation** — TS 6.x warns about `baseUrl` being deprecated. Add `"ignoreDeprecations": "6.0"` to tsconfig.json or remove baseUrl and adjust paths.
- **LLM API credits for migration** — OpenRouter may return 402 (insufficient credits) for large component migrations. Reduce `max_tokens` to 4000 or use the local Hermes gateway. MiniMax API keys may be expired — verify with a test call first.
- **Migrated component dependencies** — Components migrated from hermes-workspace reference packages not in agent-os (recharts, motion/react, @tanstack/react-query). Before integrating migrated components, install missing packages and create stub files for missing internal modules.
- **Staged component integration** — Don't drop all migrated components into the frontend at once. Migrate one page at a time (e.g., DashboardPage first), verify it builds and renders, then proceed to the next. If a page fails to build due to missing dependencies, fix those dependencies before moving on. Always run `npx tsc --noEmit` after each page replacement to catch import errors early.

## Observability

Chat events are emitted to `aie_events` table (fire-and-forget via `pgPool.query`):
- `chat_message` — emitted when user message stored (includes role, tokens, model, preview)
- `chat_response` — emitted when assistant response stored (includes role, tokens, model, preview)

Frontend can consume via `GET /api/events/recent` and `GET /api/events/agent`.

## Backup

pg_dump runs daily at 3am via host cron:
- Script: `/home/sean/.hermes/scripts/pg-backup.sh`
- Output: `/home/sean/.hermes/backups/postgres/agentos_YYYYMMDD_HHMMSS.sql.gz`
- Retention: 7 days (auto-pruned)

## hermes-web-computer Three-Column Layout (v1.2, BUILT 2026-05-11)

Three-column UI is complete and pushed to GitHub: `github.com/ChonSong/hermes-web-computer`.

**Layout:** CSS grid (`280px | 1fr | 360px`), toggleable left/right panels (Ctrl+B / Ctrl+Shift+B), drag-to-resize columns with localStorage persistence.

**Backend:** `ws/filesystem.go` (fs.list/read/write/stat with path sandboxing), `ws/apps.go` (apps.list/launch for terminal/editor/preview). All handlers routed through existing WS multiplexer ("one wire" principle).

**Frontend components:** `App.svelte` (3-column grid shell), `LeftPanel.svelte` (tabbed Files/Apps), `MiddlePanel.svelte` (tiling area), `RightPanel.svelte` (agent chat), `ResizeHandle.svelte` (drag resize), `FileTree.svelte` (WS-driven directory listing), `AppLauncher.svelte` (launch cards).

**Testing:** 45 Go unit/integration tests (all passing), 26 Playwright E2E tests passing (17 total test files). See `hermes-computer` skill for full details.

**Keyboard shortcuts:** Ctrl+K (command palette), Ctrl+? (keymap), Ctrl+B (toggle left), Ctrl+Shift+B (toggle right), Shift+D (swap split), Shift+Q (close tile), Shift+F (fullscreen).

**Bundle:** 349KB JS + 17KB CSS (within 400KB budget).

## Future Vision: Architecture Decision — RESOLVED (2026-05-11)

**Decision:** hermes-web-computer (Go+Svelte 5) is the target shell. agent-os is the legacy source for migration. hermes-agent (Python) stays separate as the AI brain.

**Rationale:** Go + Svelte 5 is the newer "lean but powerful" spec: single binary Go backend, Svelte 5 runes, no Temporal/CRDTs/AST parsers, sub-100ms interrupt, WebSocket JSON-RPC multiplexer. agent-os has 22 React pages worth migrating into hermes-web-computer as Dashboard Tile components.

**agent-os role:** Source for migration. Its 22 React pages → 3-4 Svelte 5 Dashboard Tile components (agent status, sessions, system metrics). The React+Express+PostgreSQL stack will be maintained until migration is complete, then deprecated.

**Migration path:** repo-transmute v2 handles React→Svelte 5 component migration. agent-os pages are T1 priority in the seans-reporepo candidates/ directory (2-3 days effort).

**hermes-web-computer v1.0 tiles:** Terminal (built-in) + Browser (bytebot migration) + Voice Chat (Fun-Audio-Chat) + Dashboard (agent-os migration). See `hermes-computer` skill for hermes-web-computer architecture, tile development, and the full component dependency map (`references/component-dependencies.md`). See hermes-computer-planning APPLICATION-PLAN.md for full tile specs, component wireframes, and repo-transmute commands.

**The Big Picture:** hermes-web-computer is the tiling shell, hermes-agent is the AI brain, agent-os pages become tiles. See `hermes-computer-planning/ONE-WEBSITE.md` for complete architecture analysis.

## Features List Reference

`github.com/ChonSong/features-list` contains a complete catalog of hermes-workspace + agent-os + repo-transmute v2 features, plus 100+ future ideas. See `references/features-list-catalog.md`.

## Repo-transmute Integration

Use `ChonSong/repo-transmute` (branch: `master`) for frontend migration between projects:
- `frontend_blueprint <path>` — extract components, routes, CSS, APIs
- `theme_analysis <src> -t <tgt>` — theme compatibility
- `frontend_migrate <src> <tgt> --dry-run` — full plan

- `references/cloudflare-tunnel-debug.md` — token types, DNS, credentials format, trycloudflare gotchas
- `references/hermes-webui-tunnel-restore.md` — hermes.codeovertcp.com tunnel restore: credentials reconstruction, watchdog setup, run commands, discovery via Cloudflare API

## Dockerfile Runtime Base

Use `node:22-slim` for the runtime stage (not `debian:13-slim`). See `references/node-runtime-base-pattern.md` for the full explanation.
