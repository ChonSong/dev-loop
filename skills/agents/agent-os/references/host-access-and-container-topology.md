# agent-os: Host Access & Container Topology (2026-05-07)

## SSH Access from hermes Container

**Working SSH key (confirmed 2026-05-09):**
```
/opt/data/home/.ssh/id_ed25519
```
- `/opt/data/home/.hermes/home/.ssh/id_ed25519` also works but the canonical path is above
- Port 22 is blocked on host — use port 2229: `ssh -i /opt/data/home/.ssh/id_ed25519 -p 2229 root@localhost "..."`
- `ssh sean@localhost` on default port 22 will fail — always use `-p 2229 root@localhost`
- Direct SSH is unreliable — prefer Docker socket approach: `docker -H unix:///var/run/docker.sock exec ...`

## Docker Compose Path

**Correct path on host**: `/home/sean/.hermes/agent-os/docker-compose.yml`

Other paths that exist but are NOT the running stack:
- `/opt/data/hermes-sync/projects/agent-os/docker-compose.yml` — invalid interpolation (MINIMAX_API_KEY var), not used
- `/home/sean/.hermes/hermes-sync/projects/agent-os/docker-compose.yml` — also not the running one

## Running Container Names

```
agent-os-backend        # Express backend on :3001, healthy
agent-os-nanobot        # nanobot serve on :8900, healthy
agent-os-webhook-emitter # CasaOS webhook relay, healthy
agent-os-postgres        # PostgreSQL 16-alpine, healthy
agent-os-cloudflared     # Cloudflare tunnel, healthy
```

## How to Restart a Service (e.g. add a port)

```bash
# 1. Edit docker-compose.yml on host
sed -i 's/"127.0.0.1:3001:3001"/"127.0.0.1:3001:3001"\n      - "127.0.0.1:1331:3001"/' /home/sean/.hermes/agent-os/docker-compose.yml

# 2. Recreate only that service (background)
ssh ... "cd /home/sean/.hermes/agent-os && docker compose up -d backend"

# 3. Verify
ssh ... "ss -tlnp | grep 1331"
```

## Backend API Notes

- Listens on `PORT=3001` inside container, mapped to `127.0.0.1:3001` (host)
- Serves both the TypeScript dashboard frontend (compiled dist) AND the API on the same port
- **Important**: When testing API routes with curl, ALWAYS pass `-H 'Accept: application/json'` — without it, Express serves the SPA fallback (index.html) for unknown routes, making it look broken when it's not
- Known working endpoints: `/api/status`, `/api/db/health`, `/api/sessions`, `/api/files/read/*`
- SPA catchall at `app.get('*')` returns index.html for unmatched routes

## Frontend Topology

The React frontend is compiled into `/app/apps/dashboard/frontend/dist/` inside the `agent-os-backend` container. It's served by Express's `express.static()` middleware at the root path. No separate nginx/frontend container needed.
