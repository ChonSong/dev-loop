# Deploy Webhook — /api/deploy Implementation

## Architecture

Server behind NAT → CI cannot SSH directly. CI POSTs to Cloudflare tunnel URL with deploy token. Backend returns 200 immediately, then asynchronously pulls + restarts containers via a detached child process.

**Core constraint: the backend cannot restart itself.** If the handler process dies mid-execution, the webhook fails. Always return fast, do work in background.

## Deploy Token

```bash
openssl rand -hex 32
```

Set via `DEPLOY_TOKEN` env var in `docker-compose.yml`.

## Verified-Working Handler (2026-05-06)

**Critical bug fixed:** The handler MUST call `res.json()` — without it, curl hangs forever even though the deploy actually executes. The child process was spawned correctly, but the HTTP response was never sent.

```typescript
app.post('/api/deploy', express.text(), async (req, res) => {
  const deployToken = process.env.DEPLOY_TOKEN;
  const providedToken = typeof req.body === 'string' ? req.body.trim() : '';
  if (!deployToken || providedToken !== deployToken) {
    res.status(401).json({ error: 'Unauthorized' });
    return;
  }
  try {
    const { execSync, spawn } = await import('child_process');
    const log = (msg: string) => console.log(`[deploy] ${msg}`);
    log('Starting deploy webhook handler');

    // Use docker -H to access host Docker socket from inside container
    // Socket at /var/run/docker.sock (host filesystem) is mounted rw
    const SOCK = '-H unix:///var/run/docker.sock';
    const COMPOSE = '/usr/bin/docker-compose -f /home/sean/.hermes/agent-os/docker-compose.yml';

    // Pull latest — runs via host socket, bypasses container network GHCR issue
    log('Pulling latest ghcr.io/chonsong/agent-os:latest');
    execSync(`/usr/bin/docker ${SOCK} pull ghcr.io/chonsong/agent-os:latest`, { stdio: 'ignore' });
    log('Pull complete');

    // rm -sf + up: bypasses SIGTERM 10s wait. sleep 2 ensures shell exits before SIGKILL.
    // Only restarts backend + webhook-emitter. nanobot stays untouched.
    const child = spawn('/bin/sh', ['-c',
      `sleep 2 && /usr/bin/docker ${SOCK} ${COMPOSE} rm -sf backend webhook-emitter > /dev/null 2>&1; ` +
      `/usr/bin/docker ${SOCK} ${COMPOSE} up -d backend webhook-emitter > /dev/null 2>&1`
    ], { detached: true, stdio: 'ignore' });
    child.unref();
    log('Deploy triggered (pull+rm+up in background)');
    res.json({ ok: true, received_at: new Date().toISOString() });
  } catch (err) {
    console.error('[deploy] Error:', err);
    res.status(500).json({ error: (err as Error).message });
  }
});
```

Key changes from earlier versions:
- `docker -H unix:///var/run/docker.sock` accesses host Docker from inside the container — GHCR is reachable from host network
- `rm -sf` (force, no SIGTERM) instead of `rm` (SIGTERM, 10s timeout)
- `sleep 2` before compose to ensure shell is ready when SIGKILL fires
- `res.json()` explicitly called — this was the original bug causing all timeouts
```

## Required Compose Configuration

```yaml
services:
  backend:
    image: ghcr.io/chonsong/agent-os:latest
    container_name: agent-os-backend
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:rw
      - /home/sean/.hermes/agent-os:/opt/agent-os:ro
    environment:
      DEPLOY_TOKEN: ${DEPLOY_TOKEN}
```

- **`docker.sock:rw`** — backend runs docker commands on host via socket
- **`/opt/agent-os:ro`** — compose file readable if needed
- **`DEPLOY_TOKEN`** — generate with `openssl rand -hex 32`

## Why dockerode fails here

| Approach | Problem |
|----------|---------|
| dockerode `pull()` | OOM (exit 137) — serializing large image progress stream balloons memory |
| dockerode `createContainer()` | OOM — large container config serialization |
| `docker restart` of backend | Handler process dies before `res.json()` → curl times out |
| Self-restart via dockerode | Same — handler dies mid-execution |

Fix: use `execSync('/usr/bin/docker pull ...')` (minimal memory) for pulling, and `spawn({ detached: true })` for restarting.

## Detached child process pattern

```typescript
const { spawn } = await import('child_process');
const child = spawn('/bin/sh', ['-c',
  'sleep 5 && ' +
  '/usr/bin/docker-compose -f /home/sean/.hermes/agent-os/docker-compose.yml up -d --remove-orphans backend webhook-emitter'
], { detached: true, stdio: 'ignore' });
child.unref();
res.json({ ok: true, triggered_at: new Date().toISOString() });
```

- **`detached: true`**: child outlives the handler process
- **`stdio: 'ignore'`**: prevents Node.js from buffering output in memory
- **`child.unref()`**: process doesn't wait for child to exit

## Why NOT `docker rm && docker run`

`docker run` doesn't read `environment:` from compose — must pass all env vars inline. `docker-compose up -d <service>` reads all configuration from the compose file and preserves env vars, ports, and volumes.

## Why NOT `docker-compose down && up`

`docker-compose down` removes ALL containers including postgres (data volume persists but container is gone). Use `docker-compose up -d` (no `down`) which recreates only changed containers.

## Network name: `agent-os_agent-net`

Docker Compose prefixes networks with project name. The network is `agent-os_agent-net`, not `agent-net`. Relevant if manually running `docker run --network <name>`.

## nanobot cannot be restarted by the webhook

nanobot requires credentials from `/root/.nanobot/config.json` (set by compose `environment:` at `docker-compose up`). A detached child from the backend container doesn't have these env vars — nanobot starts without API key and crashes:

```
Error: No API key configured for provider 'None'.
```

nanobot must be restarted via `docker-compose up -d nanobot` run on the **host** (where compose env vars are available), not from the backend container.

## Testing

```bash
# Health check
curl -s http://localhost:3001/api/db/health

# Wrong token → 401/403
curl -X POST http://localhost:3001/api/deploy -H 'Content-Type: text/plain' -d 'wrong'

# Correct token → returns in ~1s, containers restart async
curl -s -X POST http://localhost:3001/api/deploy \
  -H 'Content-Type: text/plain' \
  -d 'lMDaeQ5BPamS3RYnmLtvDIEd6Q5GwXER5bYi86DAjQc'

# Verify new image after 30s
docker inspect agent-os-backend --format '{{.Image}}'
docker inspect agent-os-webhook-emitter --format '{{.Image}}'
```

## CI Integration

```yaml
- name: Trigger deploy webhook
  run: |
    curl -s -X POST "${{ secrets.DEPLOY_URL }}/api/deploy" \
      -H "Content-Type: text/plain" \
      -d "${{ secrets.DEPLOY_TOKEN }}"
```

Requires `DEPLOY_TOKEN` and `DEPLOY_URL` secrets in GitHub repo → Settings → Secrets.

## Timeline

```
T+0s:    POST /api/deploy received
T+0.1s:  execSync docker pull (synchronous)
T+5s:    pull completes
T+5.1s:  spawn() detached child
T+5.2s:  res.json() returns 200  ← curl done
T+10s:   detached child runs docker-compose up -d
T+15s:   containers on new image
```

CI curl must use `--max-time 120` to exceed this window.

## Failure modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| Backend OOM on deploy (137) | dockerode pull/createContainer memory spike | Use execSync docker pull |
| Backend dies during deploy | Handler restarts itself | Return 200 before async work |
| Returns 200 but nothing restarts | Shell `&&` chain stops on error | Use docker-compose up approach |
| nanobot stuck in restart loop | nanobot restarted without API key env | Skip nanobot in compose restart list |
| Containers on old image after deploy | `docker-compose up` without prior pull | Pull explicitly before restart |
| `docker-compose: not found` | Binary not in container | Not needed — use host's docker-compose via socket |
| Webhook times out | docker-compose takes >60s | Return 200 before starting compose |
