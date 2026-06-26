# GTO Wizard Tunnel Debugging — Session Notes

## Architecture
- **Tunnel ID**: `d5046684-c9a5-459f-a128-8bbe3700a915` (gto-wizard-v3)
- **DNS**: `wiz.codeovertcp.com` CNAME → `<tunnel-id>.cfargotunnel.com` (proxied through Cloudflare)
- **Ingress**: `wiz.codeovertcp.com` → `http://172.19.0.2:8564` (container IP, NOT localhost)
- **Backend**: FastAPI on port 8002, proxied via Next.js rewrites (`/api/*` → `localhost:8002`)
- **Cloudflared binary**: `/tmp/cloudflared` (inside container AND copied to host at same path)

## Critical: API Config vs Local YAML

Cloudflare tunnels have **two layers of configuration**:

1. **Local YAML file** (e.g., `gto-wizard-config.yml`) — used at tunnel startup
2. **API-stored configuration** — pushed via `PUT /accounts/{id}/cfd_tunnel/{id}/configurations`

**THE API CONFIG OVERRIDES THE LOCAL YAML.** When the tunnel starts, it fetches the API-stored config and applies it on top of the local file.

## HTTP Status Codes for Tunnel Debugging

| Code | Meaning | Likely Cause |
|------|---------|-------------|
| 530 | Cloudflare Tunnel Error | DNS points to wrong tunnel, or tunnel not receiving traffic |
| 502 | Bad Gateway | Tunnel connected but origin unreachable from tunnel client |
| 404 | Not Found | Tunnel working, but app returns 404 |
| 200 | OK | Everything working |

## Common Problems

### DNS update reports success but doesn't actually change the record
Verify with a separate API GET call after PUT. Issue a second PUT if verification shows old value.

### Host can't reach container's localhost
`network_mode: host` does NOT expose container ports at host localhost. Use container IP (e.g. `172.19.0.2`) instead.

### Tunnel keeps dying with "control stream encountered a failure"
Run cloudflared from the **host machine** (not inside the container) via SSH. The container network may be unstable.

### "No ingress rules were defined" at startup
Normal — this fires before the API config is fetched. Verify after a few seconds that it updates to the correct config.

### DNS hostname resolution from inside container
On Arch Linux in the container, `getent hosts` works differently. Use `dig` (via `bind` package) or direct IP.
