# agent-os API Debugging Reference

## Always use `Accept: application/json`

Without this header, Express serves HTML fallback (SPA) even for valid API routes:

```bash
# WRONG — returns HTML
curl http://localhost:3001/api/status

# CORRECT — returns JSON
curl -H 'Accept: application/json' http://localhost:3001/api/status
```

## No `/api/health` route exists

The backend does NOT define `/api/health`. Requests to undefined API paths fall through to `app.get('*')` → `index.html` (SPA catchall).

**Available health-like endpoints:**
- `GET /api/db/health` → `{"ok":true,"source":"postgresql"}`
- `GET /api/status` → full gateway/platform status
- `GET /api/deploy/status` → deploy status

## Cloudflare Tunnel: Access Redirect Is Normal

`https://os.codeovertcp.com` returns HTTP 302 to `seanchasad.cloudflareaccess.com/cdn-cgi/access/login/...`

This is **expected** — tunnel is live, Cloudflare Access is enforcing auth. Tunnel logs show `Registered tunnel connection` for all 4 Cloudflare PoPs (syd01, syd07, cbr01).

## Backend Health Check (via SSH)

```bash
ssh -i /opt/data/home/.hermes/home/.ssh/id_ed25519 -o StrictHostKeyChecking=no sean@localhost \
  "curl -s -H 'Accept: application/json' http://localhost:3001/api/status"
```

## Docker Socket in hermes Container

The hermes container has no docker socket. All docker operations must go via SSH:

```bash
# FAILS in hermes container (expected)
docker ps

# WORKS via SSH to host
ssh -i /opt/data/home/.hermes/home/.ssh/id_ed25519 -o StrictHostKeyChecking=no sean@localhost "docker ps"
```
