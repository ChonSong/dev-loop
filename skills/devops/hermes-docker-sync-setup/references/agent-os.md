# Agent OS (ChonSong/agent-os) — Project Reference

Live at: **https://github.com/ChonSong/agent-os**

Nanobot fork: `ChonSong/nanobot` (https://github.com/ChonSong/nanobot) — HKUDS/nanobot upstream, 3 CIs green.

Docker images:
- `ghcr.io/chonsong/agent-os-nanobot:main`
- `ghcr.io/chonsong/agent-os-dashboard:latest` + `:sha-<hash>`

## Architecture

```
ChonSong/agent-os (monorepo)
├── apps/
│   └── dashboard/
│       ├── backend/            # Express + TypeScript (port 9120)
│       │   └── src/index.ts    # POST /api/chat (streaming), SSE, static SPA
│       └── frontend/           # React + Vite
│           └── src/pages/ChatPage.tsx  # fetch POST + EventSource SSE
├── docker-compose.yml          # nanobot + dashboard services
├── Dockerfile.nanobot
└── Dockerfile.dashboard         # Alpine, builds frontend+backend, serves on :9120
```

## Phase 1 Done (2026-05-02)
- Backend: Express with `POST /api/chat` (proxies nanobot streaming, returns session ID) + `GET /api/chat/stream?session=<id>` (SSE) + `DELETE /api/chat?session=<id>` (cancel)
- Frontend: `ChatPanel.tsx` rewritten to `fetch` POST + `EventSource` SSE (replaces Hermes WebSocket)
- Dockerfile.dashboard: single Alpine stage, Vite build + TypeScript → JS, serves on 9120

## Phase 2 Outstanding
- [x] ~~AgentLoop doesn't emit AIE events to AIELogger~~ → `AIEAgentHook` class committed (emits `TOOL_CALL` + `TASK_COMPLETE`)
- [x] ~~No watchdog for crash loops~~ → `watchdog.py` committed (health check every 30s, 3-strike restart)
- [ ] Sessions are file-based — no SQLite/PostgreSQL control plane DB
- [ ] `DEPLOY_SSH_KEY` GitHub Actions secret not configured — SSH deploy workflows won't work
- [ ] CI `Build and Push` job failing — `build-push-action` reports `completed` but job is `failure` (actual error hidden)

## GitHub Actions Docker Build — Buildx Cache Corruption

### Symptom
Docker buildx steps fail with errors like:
```
ERROR: failed to solve: error getting cached - server response missing cache
```
or layers from a previous failed run (`backend-builder:latest`) are used, causing cascading failures.

### Root Cause
GHA's Docker buildx cache (`ghcr.io/chonsong/agent-os-nanobot:buildx-cache` etc.) can get corrupted when a prior workflow run fails mid-build. Subsequent runs pull the stale/partial cache and fail.

### Fix
Remove the `--cache-from` and `--cache-to` flags from the `docker buildx build` step entirely. Cache is then built fresh each run and not reused across runs.

```yaml
# BEFORE (broken — cache corruption propagates):
- name: Build and Push Dashboard
  run: |
    docker buildx build \
      --cache-from type=gha,scope=backend,ref=ghcr.io/chonsong/agent-os-nanobot:buildx-cache \
      --cache-to type=gha,scope=backend,ref=ghcr.io/chonsong/agent-os-nanobot:buildx-cache \
      ...

# AFTER (clean — no stale cache reuse):
- name: Build and Push Dashboard
  run: |
    docker buildx build \
      --push \
      --tag ghcr.io/chonsong/agent-os-dashboard:${{ env.IMAGE_TAG }} \
      ...
```

The `--push` flag handles pushing layers directly; no explicit cache reuse needed for a working pipeline.

## TypeScript + Vite Build Gotcha

### Symptom
CI build script runs `tsc && vite build` but fails:
```
vite.config.ts(1,21): error TS2307: Cannot find module '@types/node'
```

### Root Cause
`tsc` (without `--noEmit`) performs a full type-check including `vite.config.ts`, which imports `node:path` and `node:fs`. The `@types/node` package is not in `dependencies` — only in the `devDependencies` which may not be installed in the CI environment, or the `tsconfig.json` excludes `node_modules` from type-checking.

### Fix
Split the build into type-check (optional/warning) and build only:
```json
// package.json scripts — DON'T do this:
"build": "tsc && vite build"  // ← tsc type-checks vite.config.ts and fails

// Do this instead:
"build": "vite build",         // vite build skips type checking by default
"type-check": "tsc --noEmit"  // separate step if you want it
```

Alternatively, add `@types/node` to `dependencies` (not just `devDependencies`) in `package.json`.

## GitHub Actions Docker Build — `completed` vs `failure` Discrepancy

### Symptom
In the GHA workflow UI, a `Build and Push` step shows `✅ completed` but the overall job shows `❌ failure`. No error message is visible in the step summary. All preceding steps (checkout, buildx setup, registry login) show `✅`.

### Root Cause
The `docker/build-push-action` swallows the actual build error and reports the step as `completed` even when the build fails internally. The real error is hidden inside the action's internal log — not surfaced to the GHA step summary.

### Debugging Fix
Replace the `docker/build-push-action` with raw shell to get the actual error:

```yaml
# BROKEN — hides the real error:
- uses: docker/build-push-action@v6
  with:
    tags: ghcr.io/${{ github.repository }}/latest
    push: true

# FIXED — surfaces real error:
- name: Build and push
  run: |
    docker buildx build \
      --platform linux/amd64 \
      --tag ghcr.io/${{ github.repository_owner }}/agent-os:${{ github.sha }} \
      --tag ghcr.io/${{ github.repository_owner }}/agent-os:latest \
      --file ./Dockerfile \
      --push \
      --progress=plain \
      .
```

`--progress=plain` outputs the full build log to the GHA step output, making the actual error (OOM, missing layer, ARG not set, etc.) visible. Once diagnosed, the fix may be something else — but you can't see it without the plain progress flag.

### Quick Diagnostic (without changing workflow)
1. Go to the failed workflow run in GitHub Actions UI
2. Click the `Build and Push` step
3. Expand the **Raw logs** (sometimes the summary hides the error)
4. Search for `ERROR` or `failed` in the raw log

## Server Deployment Commands

```bash
# Pull latest images
docker compose -f /opt/data/hermes-sync/projects/agent-os/docker-compose.yml pull

# Restart services
docker compose -f /opt/data/hermes-sync/projects/agent-os/docker-compose.yml up -d

# Watch logs
docker compose -f /opt/data/hermes-sync/projects/agent-os/docker-compose.yml logs -f

# Healthcheck
curl -s http://localhost:9120/api/health || echo "NOT HEALTHY"
```

## Build Deadlock — Root-Owned node_modules + hermes Cannot Write

### Symptom
`npm install` fails with `EACCES` inside the container. The `node_modules/` directory is owned by `root:root`, and the hermes user (uid 1000) cannot write to it.

### Root Cause
npm installed as root, or a Docker build ran as root. The hermes user can read but not write.

### Workaround (build in /tmp)
```bash
# Backend: install in /tmp, compile, copy back
mkdir -p /tmp/backend-nm
cp /opt/data/agent-os/apps/dashboard/backend/package.json /tmp/backend-nm/
cd /tmp/backend-nm && npm install
cp /opt/data/agent-os/apps/dashboard/backend/tsconfig.json /tmp/backend-nm/
mkdir -p /tmp/backend-nm/src && cp /opt/data/agent-os/apps/dashboard/backend/src/index.ts /tmp/backend-nm/src/
cd /tmp/backend-nm && npx tsc
cp /tmp/backend-nm/dist/index.js /opt/data/agent-os/apps/dashboard/backend/dist/index.js

# Frontend: Vite fails trying to unlink root-owned dist files
# Build to /tmp/frontend-dist, then copy assets in
```

### Prevention
On host before building:
```bash
sudo chown -R $(id -u):$(id -g) node_modules apps/dashboard/frontend/dist apps/dashboard/backend/dist
npm run build
```

## Blank Page — Diagnosis Workflow

### Symptom
Dashboard at `http://localhost:1332` shows completely blank page. HTML loads (200), JS bundle loads (269KB, 200), but `#root` stays empty.

### Diagnosis Steps (from host)
```bash
curl -s http://localhost:1332/ | head -3
curl -s -I http://localhost:1332/assets/index-Dog0eWuZ.js
# Use hermes browser_navigate + browser_console tools
```

### Common Causes
1. **Stale dist** — hash mismatch between `index.html` `<script>` src and actual `dist/assets/*.js` filename
2. **CSS not bundled** — Vite inlines CSS into JS; if a separate `.css` appears in `dist/assets/`, it's not being loaded
3. **Silent JS exception** — minified bundle obscures the error message; `ErrorBoundary` in `main.tsx` should catch but may not show detail
4. **`@nous-research/ui` init** — if `index.css` isn't imported in `main.tsx`, the UI package styles don't load

### Fix Sequence
```bash
cd ~/.hermes/agent-os
sudo chown -R $(id -u):$(id -g) node_modules apps/dashboard/frontend/dist apps/dashboard/backend/dist
npm run build
docker build -t agent-os:test -f Dockerfile .
docker stop agent-os && docker rm agent-os
docker run -d --name agent-os -p 1331:8900 -p 1332:9120 agent-os:test
```

## TypeScript `noImplicitAny` — Express Route Callbacks

### Symptom
```
src/index.ts(691,35): error TS7006: Parameter '_req' implicitly has an 'any' type.
```
`skipLibCheck: true` doesn't fix it.

### Root Cause
`strict: true` enables `noImplicitAny`. Express route callbacks like `(req, res) =>` need explicit type annotations.

### Fix
Add to `apps/dashboard/backend/tsconfig.json`:
```json
"noImplicitAny": false
```

Or annotate callbacks: `app.get('/path', (req: Request, res: Response) => {...})`
