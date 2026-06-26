---
name: deployment-patterns
description: Deployment workflows, CI/CD pipelines, Docker containerization, health checks, rollback strategies, self-hosting without Docker, and production readiness checklists.
category: devops
tags:
  - deployment
  - docker
  - self-hosting
  - ci-cd
  - fastapi
  - nextjs
source: local
is_imported: true
---

# Deployment Patterns

Production deployment workflows and CI/CD best practices, including self-hosting patterns when Docker/Redis/PostgreSQL aren't available.

## When to Activate

- Setting up CI/CD pipelines (GitHub Actions)
- Dockerizing an application for production
- Planning deployment strategy (rolling, blue-green, canary)
- Implementing health checks and readiness probes
- Making a Docker-dependent app work without Docker infrastructure
- Fixing FastAPI import-chain failures on startup
- Aligning Next.js versions in workspace monorepos

## Deployment Strategies

### Rolling (Default)
Replace containers gradually. Zero downtime, backward-compatible changes required.

### Blue-Green
Two identical environments, switch traffic atomically. Instant rollback. Requires 2x infra.

### Canary
Route small % traffic to new version first. Catches issues before full rollout.

## Self-Hosting (No Docker)

When Docker, Redis, or PostgreSQL aren't available (e.g., in a container without those services), full-stack monorepos can still run.

### Fakeredis for Redis Dependencies
Replace real Redis with fakeredis — no daemon needed, persist=False is fine for dev:
```python
def init_redis(app):
    redis_url = os.environ.get("REDIS_URL", "")
    try:
        if redis_url:
            import redis
            app.state.redis = redis.from_url(redis_url, decode_responses=True)
        else:
            import fakeredis
            app.state.redis = fakeredis.FakeRedis(decode_responses=True)
        app.state.redis.ping()
    except Exception:
        import fakeredis
        app.state.redis = fakeredis.FakeRedis(decode_responses=True)
```
Install: `pip install fakeredis sortedcontainers`. Most Redis operations (ping, get, set, publish/subscribe) work transparently.

### SQLite Fallback for PostgreSQL
Replace async PostgreSQL with async SQLite — no daemon needed, file-based:
```python
DATABASE_URL = os.environ.get("DATABASE_URL", "")
if not DATABASE_URL:
    DATABASE_URL = f"sqlite+aiosqlite:///{os.path.abspath('app.db')}"
```
Install: `pip install aiosqlite`. Strip `pool_size`/`max_overflow` flags (SQLite doesn't support them). SQLAlchemy `create_async_engine(URL)` works identically. PostgreSQL-only features (JSONB, array columns, ILIKE) will fail at runtime — keep models compatible.

### Absolute Binary Paths for Background Processes
Background processes (`terminal(background=True)`) start in a minimal shell without the user's PATH. Shebang-based scripts (`#!/usr/bin/env node`) fail with "No such file or directory":
```python
# Wrong: terminal("npx next start -p 3000", background=True)  # fails
# Right: use absolute binary paths
node = "/home/hermeswebui/.hermes/home/.local/bin/node"
next_bin = "/workspace/project/node_modules/next/dist/bin/next"
terminal(f"cd {web_dir} && {node} {next_bin} start -p {port}", background=True)
```

### Next.js: Stale Bundle After Build (No Docker)

When running `npx next start` as a standalone process (not Docker), `npx next build` writes new chunks to `.next/` but the running `next-server` keeps the OLD bundle in memory. The browser keeps receiving the old `page-<old_hash>.js`. The fix is to kill the old process and restart:

```bash
# Find the process
ps aux | grep 'next.*3000\|next start' | grep -v grep

# Kill AND start fresh
kill <PID>
npx next start -p 3000 &

# Verify new bundle is served
curl -s http://localhost:3000/study | grep -oP 'page-[^"]+'
```

**Do NOT rely on the process having the same PID after restart.** Without this step, deploys are silent no-ops — the build succeeds, the logs say nothing, but users see the same old page for days.

#### Systemd-Managed Next.js — Additional Steps

When the Next.js server runs as a `systemctl --user` service (e.g., `gto-wizard-web.service`), `kill <PID>` is **not sufficient** — systemd respawns the old process instantly from its original `ExecStart` line. The fix is to restart via systemd after the build:

```bash
# Build first
cd apps/web && npx next build

# Then restart the systemd service — kill + respawn the right process
systemctl --user restart gto-wizard-web.service

# Verify: check the JS bundle hash served vs what was built
curl -s http://localhost:3000/study | grep -oP 'page-[^"]+'
# Expected: matches ls .next/static/chunks/app/study/page-*.js
```

**Pitfall:** Checking only port occupancy (`fuser 3000/tcp`, `ss -tlnp | grep 3000`) shows *a* process is listening but gives no indication it's the old build. The new JS bundle hash differs — always verify the bundle hash matches the built file. A `process(action='wait')` that exits cleanly on port 3000 may actually have been beaten by the systemd-respawned stale process that grabbed the port first.

**Signs you're hitting this:**
- Build logs show "✓ Compiled successfully" but page looks identical
- Browser devtools show an old `page-<hash>.js` that no longer exists in `.next/`
- `curl -s http://localhost:3000/study | grep -oP 'page-[^"]+'` returns a hash not found in `.next/static/chunks/app/study/`
- `fuser -k 3000/tcp && sleep 1 && fuser 3000/tcp` still shows a process — systemd respawned it
A monorepo with `"workspaces": ["apps/*","packages/*"]` can pull in two different Next.js versions (root `^16.x`, workspace `^15.x`). This causes Turbopack crashes with `File not found: server-external-packages.jsonc`. Fix: align root `package.json` next version to match the workspace.

Build fallback for pre-existing type conflicts (esModuleInterop, @types/react, workbox types):
```javascript
// next.config.ts
const nextConfig = {
  typescript: { ignoreBuildErrors: true },
}
```

### Python FastAPI Import Chain Debugging
When `uvicorn main:app` fails to start:
- **NameError**: A symbol used at module level is only imported inside a function body (e.g., `SpotCategory` used in `_get_spot_description()` but imported only in another route handler). Fix: add the import at the top of the file.
- **AttributeError: no attribute 'router'**: A helper/library module was added to `app.include_router()`. Fix: remove the import and `include_router` line for that module.

## Multi-Stage Dockerfiles

### Node.js
```dockerfile
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --production=false

FROM node:22-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
RUN addgroup -g 1001 -S app && adduser -S app -u 1001
USER app
COPY --from=builder --chown=app:app /app/node_modules ./node_modules
COPY --from=builder --chown=app:app /app/dist ./dist
ENV NODE_ENV=production
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -qO- http://localhost:3000/health || exit 1
CMD ["node", "dist/server.js"]
```

### Go
```dockerfile
FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /server ./cmd/server

FROM alpine:3.19 AS runner
RUN apk --no-cache add ca-certificates
RUN adduser -D -u 1001 appuser
USER appuser
COPY --from=builder /server /server
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://localhost:8080/health || exit 1
CMD ["/server"]
```

## Self-Hosted Go + Frontend Service (No Docker)

Full workflow to deploy a Go backend with a JS/Svelte/React frontend as a native systemd user service — no Docker required. Useful when the host lacks Docker, or you want zero-overhead process management.

For Python/uv-based backends, see `references/python-uv-systemd-user-service.md`.

For Vite static preview (games, SPAs, dashboards), see `references/vite-systemd-user-service.md`.

### Go Toolchain Install (User-Local)

```bash
# Download Go tarball (no sudo needed)
curl -sL https://go.dev/dl/go1.22.5.linux-amd64.tar.gz -o /tmp/go.tar.gz
tar -C $HOME -xzf /tmp/go.tar.gz
export PATH=$HOME/go/bin:$PATH

# Build static binary (no glibc dependency)
cd backend && CGO_ENABLED=0 go build -o agent-os ./cmd/server
# Verify: file agent-os → "statically linked"
```

### Node.js Toolchain Install (User-Local)

```bash
# Download Node 20 binary tarball (no sudo needed)
curl -sL https://nodejs.org/dist/v20.20.0/node-v20.20.0-linux-x64.tar.xz -o /tmp/node20.tar.xz
tar -xf /tmp/node20.tar.xz -C $HOME
export PATH=$HOME/node-v20.20.0-linux-x64/bin:$PATH

# Build frontend
cd frontend && rm -rf node_modules package-lock.json  # fresh install needed when Node version changes
npm install && npm run build
# Output: dist/index.html + dist/assets/
```

### Systemd User Service Unit

```ini
[Unit]
Description=My Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/home/sc/repos/my-project/backend/agent-os
WorkingDirectory=/home/sc/repos/my-project/backend
Restart=on-failure
RestartSec=5
Environment=PORT=3005
Environment=SOME_CONFIG=value

[Install]
WantedBy=default.target
```

**Key: `WorkingDirectory` matters.** The binary resolves `../frontend/dist` relative to its own CWD. If the frontend dist is at `frontend/dist/` from repo root, set CWD to `backend/` so `../frontend/dist` resolves correctly.

### Enable and Start

```bash
mkdir -p ~/.config/systemd/user
# Write unit to ~/.config/systemd/user/my-service.service

systemctl --user daemon-reload
systemctl --user enable my-service.service
systemctl --user start my-service.service

# Verify
systemctl --user status my-service.service --no-pager
curl -s -o /dev/null -w "HTTP %{http_code} in %{time_total}s" http://localhost:3005/
curl -s http://localhost:3005/health
```

### Health Endpoint Convention

Every backend should expose `GET /health` returning HTTP 200 with body `ok` or `{"status":"ok"}`. Systemd doesn't natively health-check user services, but the endpoint enables monitoring via cron or external load balancers.

### Pitfalls

| Pitfall | Fix |
|---------|------|
| `GLIBC_X.Y not found` on binary | Build with `CGO_ENABLED=0` for static linking |
| `@tailwindcss/oxide` native bindings fail on Node 18 | Use Node 20+ for frontend builds |
| Binary built on one host has wrong glibc | Always build on target, or use static linking |
| `npm install` after Node version change | `rm -rf node_modules package-lock.json && npm install` |
| systemd `WorkingDirectory` resolves `../frontend/dist` wrong | Set CWD to the backend dir, not repo root |
| Binary starts but 404 on `/` | Check the static file serving path — frontend dist not found |

## User-Level Log Rotation (No Sudo)

When you can't `sudo` to install logrotate configs in `/etc/logrotate.d/`, run logrotate from a user-owned config directory with a cron trigger.

### Setup

```bash
# 1. Create user config dir
mkdir -p ~/.config/logrotate

# 2. Write config (copytruncate for open-file-handle apps)
cat > ~/.config/logrotate/my-service.conf << 'CONF'
/home/sc/.hermes/logs/my-service.log {
    rotate 4
    size 1M
    daily
    compress
    copytruncate
    missingok
    notifempty
}
CONF

# 3. Run once to test
logrotate --state ~/.logrotate.state -f ~/.config/logrotate/my-service.conf

# 4. Verify rotation
ls -lh /home/sc/.hermes/logs/my-service.log*   # should show .log.1.gz
```

### Cron Schedule

Create a daily cron job:

```
schedule: "0 6 * * *"   # daily at 06:00
prompt: Run: logrotate --state ~/.logrotate.state ~/.config/logrotate/my-service.conf
```

### Key Options

| Option | When |
|--------|------|
| `copytruncate` | App keeps the log file open (writes to same FD) — copies content then truncates in-place |
| `compress` | Gzips old logs (saves ~95% space — 1.6M → 60K) |
| `size 1M` / `size 100M` | Rotate when log reaches threshold (overrides `daily` if hit sooner) |
| `rotate 4` | Keep 4 compressed archives |
| `missingok` | Don't error if log doesn't exist yet |
| `notifempty` | Skip rotation if log is empty |

### Pitfalls

| Pitfall | Fix |
|---------|------|
| `copytruncate` causes minor data loss between copy and truncate | Acceptable for deploy/batch logs; use `create` (rename + new file) for strict logs |
| System `logrotate` cron at `/etc/cron.daily/logrotate` runs as root and ignores user configs | Create a Hermes cron job for the user-level config |
| `logrotate --state` file doesn't exist | It's created automatically on first run |
| Config path wrong — `logrotate: error: stat of config file failed` | Use absolute paths in config AND command |

## CI/CD Pipeline (GitHub Actions)

```yaml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build & Push
        run: |
          docker build -t ghcr.io/${{ github.repository }}:${{ github.sha }} .
          echo "${{ secrets.GITHUB_TOKEN }}" | docker login ghcr.io -u $GITHUB_ACTOR --password-stdin
          docker push ghcr.io/${{ github.repository }}:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: SSH Deploy
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.DEPLOY_HOST }}
          key: ${{ secrets.DEPLOY_KEY }}
          script: |
            cd /opt/app
            docker pull ghcr.io/${{ github.repository }}:${{ github.sha }}
            docker compose up -d --force-recreate
            sleep 5
            curl -f http://localhost:3000/health || exit 1
```

## Health Checks

- **HTTP endpoint**: `/health` returning 200 with body `{"status":"ok"}`
- **Readiness probe**: checks dependencies (DB, Redis, etc.)
- **Liveness probe**: process is alive (simple 200)
- **Interval**: 30s, timeout 3s, retries 3, start-period 5s

## Rollback Strategy

1. Keep previous image tag available
2. `docker compose up -d --force-recreate` with previous tag
3. Verify health endpoint
4. If rollback fails, alert via Telegram/Discord

## No-Agent Deploy Watchdog (Cron + Script)

A cron job with `no_agent=true` runs a shell script on schedule with zero LLM cost. The script's stdout is delivered verbatim to the user. Non-zero exit sends an error alert.

**Use for:** build-test-deploy loops, health checks, watchdog alerts, API polling.

**Delivery semantics:**
- Non-empty stdout → sent verbatim
- Empty stdout → silent (nothing sent) — the classic watchdog pattern
- Non-zero exit → error alert
- Timeout → error alert

### Script Template

```bash
#!/bin/bash
set -e
cd /home/sc/repos/my-project

BUILD_OK=$(npm run build 2>&1 | grep -c "built in")
echo "BUILD:$BUILD_OK"

if [ "$BUILD_OK" -eq 0 ]; then exit 1; fi

# Vite preview as dev server — auto-restart if down
if ! curl -sf http://localhost:3001/ > /dev/null 2>&1; then
  nohup npx vite preview --port 3001 --host > /tmp/preview.log 2>&1 &
  sleep 3
fi

echo "DEPLOY_OK"
```

### Cron Setup

```
action: create
name: My Project deploy loop
no_agent: true
schedule: "every 5m"
script: deploy-watchdog.sh
```

### Chaining

Chain a no-agent data collector with an LLM summarizer via `context_from`:

1. Job A (no_agent=true): polls API, writes result to stdout
2. Job B (no_agent=false): reads Job A's last output via `context_from: [<job-a-id>]`, summarizes it

See `browser-game-dev` skill's `references/deploy-watchdog-pattern.md` for detailed examples.

When a background task (CFR solver, ML training, report generation) needs to
stream progress to a browser, use the Celery → Redis pub/sub → WebSocket bridge.
See `references/celery-redis-pubsub-bridge.md` for the full pattern.  
See `references/python-uv-systemd-user-service.md` for deploying Python/uv apps as user-level systemd services (no sudo).

Key points:
- Worker publishes typed messages (`solve:progress` / `solve:complete` / `solve:error`) to Redis channel `solver:progress:{job_id}`
- API RedisService caches latest status + final result
- WebSocket endpoint subscribes to the channel and forwards to client
- gRPC is NOT appropriate for browser-facing patterns (browsers can't speak HTTP/2)
- Never hardcode `localhost` in worker Redis URLs — use `REDIS_URL` env var

## Pre-Deploy Checklist (Production Gate)

- [ ] All tests pass (unit + E2E)
- [ ] Turbo cache cleared after route changes — Next.js + Turbo caches aggressively. Adding new routes after the initial build may not appear in production if `.next/` and `.turbo/` caches are stale. Fix: `rm -rf apps/web/.next apps/web/.turbo` before `npm run build`. Without this, the build reports success but new pages return 404.
- [ ] No suppressed build errors (check `ignoreBuildErrors`, `skipLibCheck`, `allowUnreachableCode`, etc.)
- [ ] Dependencies install cleanly (`npm ci` / `pip install -r` produces no errors)
- [ ] No security vulnerabilities (npm audit / pip audit / gosec)
- [ ] Docker image builds, OR standalone self-hosting path works
- [ ] Health endpoint works locally
- [ ] Environment variables documented in `.env.example`
- [ ] Database migrations tested, OR SQLite fallback configured
- [ ] Production config doesn't contain debug/dev overrides
- [ ] Cloudflare tunnel / reverse proxy ingress configured for both UI and API routes
  - For local config.yml approach: `cloudflared tunnel --config ~/.cloudflared/config.yml run <name>`
  - See `browser-game-dev` skill's `references/cloudflare-tunnel-local-config.md`
- [ ] Rollback plan verified
- [ ] Rollback plan verified

- [ ] For Go JS + Python monorepos: both dependency trees synced (`npm install` + `uv sync --group runtime`). A frontend-only deploy that forgets to sync backend deps crashes the API silently — the server starts (uvicorn loads) but every endpoint returns `ModuleNotFoundError` or `Internal Server Error`. Check the API journal: `journalctl --user -u <api-service> --since "5 min ago" --no-pager` for tracebacks.
  - **Pitfall**: `pyproject.toml` may declare deps under `[dependency-groups]` (not `[project]`). Use `uv sync --group runtime` not bare `uv sync` to pick them up.
  - **Pitfall**: `uv pip install pkg` installs to the system venv, not the project `.venv`. Use `cd /project && uv sync --group runtime` from project root.

If any box is unchecked, flag it as a deploy blocker. Do not ship past unchecked items.

## Codebase Readiness Assessment

When taking over an existing codebase, assessing deploy-readiness, or planning the first delivery sprint, run this systematic assessment. It catches the silent failures that CI won't find.

### Phase 1: High-Level Survey

Start with the README, package.json/pyproject.toml, and any SPEC/SCOPE docs:

```bash
# What is this app? What does it do?
head -50 README.md

# What language, framework, build system?
cat package.json  # or pyproject.toml, Cargo.toml, go.mod

# Is there an architecture doc? A SPEC? A plan?
find . -maxdepth 2 -name "SPEC.md" -o -name "ARCHITECTURE.md" -o -name "DEVELOPMENT_PLAN.md" -o -name "SCOPE.md" | head -5

# What commands does it expose?
grep -A5 '"scripts"' package.json 2>/dev/null
```

### Phase 2: Environment Inventory

Check what's available to run the app:

```bash
# Runtime versions
node --version 2>/dev/null
python3 --version 2>/dev/null
go version 2>/dev/null
rustc --version 2>/dev/null

# Package managers
npm --version 2>/dev/null
pnpm --version 2>/dev/null
pip3 --version 2>/dev/null
cargo --version 2>/dev/null

# Infrastructure tools
docker --version 2>/dev/null
cloudflared version 2>/dev/null
which systemctl 2>/dev/null

# Resource limits
nproc
free -h | grep Mem
df -h / | tail -1
```

**Key signals:** Missing runtimes block the build. Ancient Python (3.8 vs required 3.11) blocks solver/ML backends.

### Phase 3: Dependency Audit

Install deps and check for problems:

```bash
# Node projects
npm ci 2>&1 | tail -20
# Or pnpm install / yarn --frozen-lockfile

# Python projects
pip install -r requirements.txt 2>&1 | tail -10
# Or: uv sync / poetry install

# Check for unmet dependencies
npm ls --depth=0 2>/dev/null | grep -i "UNMET\|MISSING\|ERR"
```

**Key signals:** Any UNMET DEPENDENCY is a blocker. Check `.env.example` for required environment variables. Check if `typescript.ignoreBuildErrors: true` or `strict: false` is hiding real issues.

### Phase 4: Build Verification

```bash
# Attempt a build
npm run build 2>&1 | tail -30
# Or: tsc --noEmit, cargo build, go build ./...
```

**Key signals:** Suppressed errors in build config (`ignoreBuildErrors: true`, `skipLibCheck: true`) mean the build passes but ships with latent type errors. Fix, don't work around.

### Phase 5: Infrastructure Scan

```bash
# What's running on what ports?
ss -tlnp 2>/dev/null | grep -v '127.0.0.53'

# Is the tunnel active?
cloudflared tunnel list 2>/dev/null
ps aux | grep cloudflared | grep -v grep

# Is there a tunnel config? What does it route?
cat ~/.cloudflared/config.yml 2>/dev/null | grep -A1 "hostname:\|service:"

# Are there systemd services?
ls /etc/systemd/system/cloudflared* 2>/dev/null
sudo systemctl list-units --type=service --state=running 2>/dev/null | grep -E "cloudflared|nginx|docker"
```

**Key signals:** Tunnel listed but zero connections = DNS resolves but nothing is served. Tunnel config has ingress rules but no matching local services = all subdomains return 404. Multiple stale tunnels from past experiments.

### Phase 6: Test Health Review

```bash
# Run the test suite
npm test 2>&1 | tail -20
# Or: pytest, cargo test, go test ./...

# Check for test directories and config
ls -la playwright.config.ts 2>/dev/null
ls -la jest.config.* 2>/dev/null
find . -name "e2e" -type d -maxdepth 3 2>/dev/null

# Check for visual regression setup
grep -r "toHaveScreenshot\|toMatchSnapshot\|pixelmatch" --include="*.ts" --include="*.js" . 2>/dev/null | head -5

# Check for existing test failures
find . -path "*/test-results/*" -name "*.md" 2>/dev/null | head -5
```

**Key signals:** E2E tests that fail on "Cannot navigate to invalid URL" suggest a base URL config mismatch. No visual regression = UI regressions will ship silently. Test results directory with error-context files means failures were never fixed.

### Phase 7: Report & Priority Synthesis

```markdown
## Readiness Assessment

### Blocker (must fix before deploy)
- Issue: [specific problem]
- Evidence: [command output, file content]
- Fix: [specific action]

### High Priority (fix before next deploy)
- Issue: [specific problem]

### Low Priority (technical debt)
- Issue: [specific problem]

### Deploy Ready Checklist
- [x] Dependencies install cleanly
- [x] Build succeeds
- [ ] E2E tests passing
- [ ] Tunnel active
- [ ] Services running
- [ ] Visual regression baseline exists
```

### Phase 8: Extract Repeatable Process

After the assessment, document the development methodology patterns found:

- **SPEC-driven**: Does the repo have a SPEC.md or architecture document that drove development?
- **Phase-based**: Were features delivered in tracked phases?
- **External libs**: Did they adapt existing code rather than write from scratch?
- **QA depth**: Are there E2E tests? Visual regression? Unit tests per component?
- **Deploy pattern**: Docker Compose? Helm? Manual? One-command deploy?

These form the "process DNA" — the repeatable methodology to apply to the next project.

See `references/codebase-readiness-assessment.md` for the full checklist template with worked examples.

## Container-to-Host Migration (Docker → Native Systemd)

Migrate a service running inside a Docker container to run natively on the host via systemd. Useful when container overhead is unwanted, volume mounts are fragile, or you need direct filesystem/hardware access.

### Discover the Bind Mount Mapping

The container's `/opt/data` may be a bind mount from a host path. Map it before writing any migration scripts:

```bash
# From inside the container — findmnt shows real source path
findmnt | grep '/opt/data'
# → /dev/sda5[/home/sc/.hermes]    host path is /home/sc/.hermes

# Alternative: /proc/mounts shows mount info
cat /proc/mounts | grep '/opt/data'

# Find container ID from cgroup
cat /proc/1/cgroup | head -1
# → /docker/5b7043177bfe...        container ID
```

**Key insight:** The host path (e.g., `/home/sc/.hermes`) is where the persistent data already lives — the container just has a bind-mounted view. No data copy needed.

### Write Migration Script to Shared Mount

Write a self-contained bash script to the bind-mounted path. It lands on the host filesystem automatically:

```bash
# Inside container — write to shared path, it appears on host
cat > /opt/data/migrate-to-host.sh << 'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
DOCKER_CONTAINER="${DOCKER_CONTAINER:-hermes}"

# 1. Install service on host
command -v hermes || uv tool install hermes-agent

# 2. Create systemd user service
mkdir -p "$HOME/.config/systemd/user"
cat > "$HOME/.config/systemd/user/my-service.service" << 'UNIT'
[Unit]
Description=My Service
After=network-online.target
[Service]
Type=simple
ExecStart=%h/.local/bin/my-service
Restart=always
RestartSec=5
[Install]
WantedBy=default.target
UNIT

# 3. Stop Docker container
docker stop "$DOCKER_CONTAINER" 2>/dev/null || true
docker update --restart=no "$DOCKER_CONTAINER" 2>/dev/null || true

# 4. Start via systemd
systemctl --user daemon-reload
systemctl --user enable --now my-service.service
SCRIPT
chmod +x /opt/data/migrate-to-host.sh
```

Ask the user to run it from the host: `bash /home/sc/.hermes/migrate-to-host.sh`

### Fix Cron Workdirs Post-Migration

Cron jobs referencing container-only paths (`/workspace`, `/home/hermeswebui/.hermes/`) break on host. **But workdirs are only half the problem** — the prompts themselves often reference container paths, and supporting scripts called by cron jobs may too.

#### Full Audit Technique

**Phase 1 — Audit all three layers:**

```bash
# 1. Check workdirs
hermes cron list | grep -E '/workspace|/home/hermeswebui|/opt/data|172\.19'

# 2. Check prompts for container path references
cat ~/.hermes/cron/jobs.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
container_paths = ['/home/hermeswebui', '/workspace', '/opt/data', '/home/hermes', '172.19.0.1', 'docker gateway']
for j in data['jobs']:
    prompt = j.get('prompt') or ''
    pwd = j.get('workdir') or ''
    found = [cp for cp in container_paths if cp in prompt or cp in pwd]
    if found:
        print(f'{j[\"name\"]}: {found}')
"

# 3. Check supporting scripts called by cron jobs
grep -rnl 'hermeswebui\|/workspace\|172\.19\.0\.1\|/opt/data' ~/.hermes/scripts/ 2>/dev/null | grep -v '.pyc'
```

**Phase 2 — Common path mappings:**

```
Container path                     → Host path
─────────────────────────────────   ─────────────────────────
/home/hermeswebui/.hermes          → $HOME/.hermes (or /home/sc/.hermes)
/home/hermeswebui/.hermes/skills   → $HOME/.hermes/skills
/workspace/seans-reporepo          → $HOME/repos/seans-reporepo
/workspace/<project>               → $HOME/repos/<project>
/workspace/MEMORY.md               → $HOME/.hermes/memories/MEMORY.md
/workspace/SOUL.md                 → $HOME/.hermes/SOUL.md
/workspace/USER.md                 → $HOME/.hermes/memories/USER.md
/workspace/qa-reports/             → $HOME/.hermes/workspace/qa-reports/
172.19.0.1 (Docker gateway)        → localhost (we're on host now)
/opt/data                          → $HOME/.hermes
```

**Phase 3 — Bulk fix via jobs.json edit:**

Edit the JSON directly with Python for efficiency (avoids 15+ CLI calls):

```python
import json

with open('/home/sc/.hermes/cron/jobs.json') as f:
    data = json.load(f)

# Path mappings (order matters — more specific first)
prompt_map = [
    ('/home/hermeswebui/.hermes/hermes-web-computer', '/home/sc/repos/hermes-web-computer'),
    ('/home/hermeswebui/.hermes', '/home/sc/.hermes'),
    ('/workspace/MEMORY.md', '/home/sc/.hermes/memories/MEMORY.md'),
    ('/workspace/SOUL.md', '/home/sc/.hermes/SOUL.md'),
    ('/workspace/USER.md', '/home/sc/.hermes/memories/USER.md'),
    ('/workspace/seans-reporepo', '/home/sc/repos/seans-reporepo'),
    ('/workspace/', '/home/sc/repos/'),  # generic fallback — check first
    ('172.19.0.1', 'localhost'),
]

def fix_prompt(text):
    for old, new in prompt_map:
        text = text.replace(old, new)
    return text

for j in data['jobs']:
    # Fix workdir
    wd = j.get('workdir')
    if wd:
        for old, new in prompt_map:
            wd = wd.replace(old, new)
        j['workdir'] = wd if wd else None
    
    # Fix prompt  
    if j.get('prompt'):
        j['prompt'] = fix_prompt(j['prompt'])

with open('/home/sc/.hermes/cron/jobs.json', 'w') as f:
    json.dump(data, f, indent=2)
```

Also fix container context lines in prompts (e.g. "You run inside the Hermes container" → "You are running on the host").

**Phase 4 — Fix supporting scripts:**

After the cron jobs, check each script that was referenced:
- `hermes-backup.sh` — fix `HERMES_HOME` auto-detection
- `skill-selector-prep.py` — may need full rewrite to remove SSH-to-host patterns
- Scripts using `172.19.0.1` — switch to `localhost`
- Scripts that SSH to host (no longer needed) — switch to direct execution

**Phase 5 — Verify:**

```bash
# Syntax check scripts
bash -n ~/.hermes/scripts/hermes-backup.sh
python3 -c "import ast; ast.parse(open('...').read())"

# Check no stale paths remain
cat ~/.hermes/cron/jobs.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
stale = ['/home/hermeswebui', '/workspace', '/opt/data', '172.19.0.1', 'docker gateway']
for j in data['jobs']:
    text = (j.get('prompt') or '') + (j.get('workdir') or '')
    found = [s for s in stale if s in text]
    if found:
        print(f'{j[\"name\"]}: {found}')
"

# Reload cron scheduler
hermes cron tick --accept-hooks
```

### Revert Plan

Always provide a revert path:

```bash
systemctl --user stop my-service
docker start "$DOCKER_CONTAINER"
```

### Key Pitfalls

| Pitfall | Fix |
|---------|------|
| No SSH on host — can't exec from container | Write script to shared mount, user runs it |
| Docker socket not mounted — can't stop container | Script runs on host where Docker is available |
| Cron workdirs point to container paths | Audit and update jobs.json post-migration |
| Container uses s6 init, not systemd | Migration creates proper systemd units |
| systemd user services need linger | `loginctl enable-linger $USER` if boot start needed |

## One-Command Bootstrap Install (`curl | bash`)

A `curl | bash` bootstrap deploys the full stack from scratch on any machine.

## Recovery from /tmp Wipe (tmpfs Projects)

When a project checked out under `/tmp/` disappears (tmpfs cleared on reboot):

### Assessment
```bash
# Check if project directory exists
ls /tmp/PROJECT_NAME/ 2>/dev/null || echo "WIPED"

# Check for orphaned processes still running from old location
ps aux | grep -E 'next start|uvicorn' | grep -v grep
# These will keep running because the file handles are still open,
# but the working directory /proc/PID/cwd will show the stale path
```

### Recovery Sequence (Next.js + FastAPI monorepo example)

```bash
# 1. Re-clone
cd /tmp
gh repo clone OWNER/PROJECT

# 2. Build frontend
cd apps/web
npm install && npm run build
nohup npx next start -p PORT > /tmp/frontend.log 2>&1 &

# 3. Install Python deps (handle known pitfalls)
cd /path/to/repo
pip install --break-system-packages -e packages/core  # edgy local dep
pip install --break-system-packages missing-module1 missing-module2
pip install 'sqlalchemy>=2.0.36'  # Python 3.13 compat — see pitfall

# 4. Start API server (monorepo PYTHONPATH)
cd /tmp/repo
PYTHONPATH=/tmp/repo:/tmp/repo/apps/api \
  nohup python -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8003 > /tmp/api.log 2>&1 &

# 5. Restart/reconfigure tunnel if ingress changed
```

### Known Python 3.13 Pitfalls
- **SQLAlchemy < 2.0.36** crashes with `AssertionError: Class SQLCoreOperations directly inherits TypingOnly`. Fix: `pip install 'sqlalchemy>=2.0.36'`
- **asyncpg** fails to compile on plain Arch (needs postgresql-libs). Skip if using fakeredis/aiosqlite.
- **Monorepo PYTHONPATH**: Set both repo root AND apps/api for imports like `from apps.api.websocket.manager` + `from routers import equity` to both resolve.

### When to Use This Pattern
The project was in `/tmp` (tmpfs) and got wiped. The original running process(es) were killed (by reboot, or by you), giving you a clean slate. Work through the recovery steps above, then verify from the tunnel endpoint.

### PAT via Credential Helper
Never embed tokens in URLs. Use git's credential helper:
```bash
if [ -z "$GITHUB_TOKEN" ]; then
  echo "ERROR: GITHUB_TOKEN not set. Usage: export GITHUB_TOKEN=ghp_... && curl ... | bash"
  exit 1
fi
git config --global credential.helper "store"
echo "https://${GITHUB_TOKEN}@github.com" > ~/.git-credentials
```

**Token scoping:** PAT needs `repo` scope. Must be `export`ed before pipe — `GITHUB_TOKEN=xxx curl ... | bash` fails because shell variables don't propagate through pipes.
```bash
# Correct:
export GITHUB_TOKEN=ghp_xxx && curl -fsSL https://raw.githubusercontent.com/OWNER/bootstrap/main/setup.sh | bash
# Wrong:
GITHUB_TOKEN=ghp_xxx curl -fsSL https://raw.githubusercontent.com/OWNER/bootstrap/main/setup.sh | bash
```

### Bootstrap Architecture
```
hermes-bootstrap (public repo)
  setup.sh                    # clones repos, configures, starts
      +-- hermes-sync (private, PAT-gated)
      |     docker/ config.yaml secrets.age .env skills/ memory/ workspace/
      +-- hermes-agent (public fork or upstream)
      +-- hermes-webui (public fork)
```

### Critical: Files Must Be Committed
Setup.sh cannot `git add` files after cloning. Critical files like `docker/` must be committed to the repo before bootstrap clones it.

### Verifying Bootstrap
Test in ephemeral environment using the actual `curl | bash` flow. Catches token-scoping, missing files, and network blocks.

### Remote File Appears Missing
Check `gh api repos/OWNER/REPO/git/trees/HEAD?recursive=1` to verify committed at remote HEAD. Local working tree ≠ remote HEAD.
