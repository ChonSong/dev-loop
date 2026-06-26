# agent-os Deployment State — May 2026

## Actual Deployed Ports

The gateway's embedded reverse proxy serves:
- `http://localhost:3000` → frontend (returns dashboard HTML)
- `http://localhost:3001` → backend (returns dashboard HTML on ALL routes = API server down/stubbed)

**Cloudflare tunnel** routes `os.codeovertcp.com` → `localhost:8642` (returns `404: Not Found`).

## Gateway Health State

From `gateway_state.json`:
```
"api_server": {"state": "retrying", "error_message": "failed to reconnect"}
"discord": {"state": "connected"}
```

The `api_server` platform is retrying — gateway can't reconnect to the backend. This means the embedded proxy (`localhost:3000 → localhost:3001`) has the backend as a target that's either down or returning HTML instead of JSON.

## Quick Health Probe

```python
import urllib.request

targets = [
    (3001, '/api/health', 'backend JSON'),
    (3000, '/', 'frontend HTML'),
    (8642, '/', 'cloudflare tunnel target'),
]

for port, path, desc in targets:
    try:
        r = urllib.request.urlopen(f'http://localhost:{port}{path}', timeout=3)
        body = r.read(300).decode('utf-8', errors='replace')
        ct = r.headers.get('Content-Type', '?')
        is_html = '<html' in body.lower() or '<!doctype' in body.lower()
        print(f":{port}{path} [{desc}] → HTTP {r.status} | {ct} | HTML={is_html} | {body[:80]}")
    except Exception as e:
        print(f":{port}{path} [{desc}] → DOWN: {e}")
```

Expected: `:3001/api/health` → JSON (not HTML). If it returns HTML, the backend API server is not running.

## Docker Compose Stack

**Live compose file:** `/opt/data/hermes-sync/projects/agent-os/docker-compose.yml`

**Service ports in compose:** 8900/9120/8901 (nanobot/internal) — these are the INTERNAL container ports. The host ports that actually work are 3000/3001 (mapped elsewhere in gateway/nginx config).

**To restart the stack:**
```bash
ssh -i /opt/data/home/.hermes/home/.ssh/id_ed25519 -o StrictHostKeyChecking=no -o BatchMode=yes sean@localhost \
  "cd /home/sean/.hermes/hermes-sync/projects/agent-os && docker compose up -d --force-recreate"
```

## Docker Containers Not Running

`docker ps` returns empty — the agent-os docker-compose stack is not currently running. This explains why:
- No nanobot process
- No postgres
- No nginx on 8080
- The ports 3000/3001 that DO respond are served by the hermes gateway itself (its embedded reverse proxy/Nginx), not by the docker stack.

## SSH Command

Always use `-o BatchMode=yes` to fail fast if SSH agent isn't forwarded:
```bash
ssh -i /opt/data/home/.hermes/home/.ssh/id_ed25519 -o StrictHostKeyChecking=no -o BatchMode=yes sean@localhost "<command>"
```

## CI Ports Confusion

CI and local builds produce ports 8900/9120/8901 inside containers. The gateway proxies these to 3000/3001 on the host. When diagnosing, always check the ACTUAL host port (3000/3001), not the internal container ports.
