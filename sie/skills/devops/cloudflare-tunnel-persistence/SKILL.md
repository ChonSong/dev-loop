---
name: cloudflare-tunnel-persistence
description: Manage Cloudflare tunnels + host services for wiz/onetag/skills/hwc domains via systemd
---

# Cloudflare Tunnel Persistence — Single-Tunnel Architecture

## Architecture
A **single Cloudflare tunnel** (`codeovertcp`, tunnel ID `ddaeb2d9`) routes all domains via a local `config.yml` ingress file. The tunnel runs as a raw process (not systemd-managed anymore) and is started with `terminal(background=true)`.

All backend services run as systemd user services (`systemctl --user`) on the host.

## Single Tunnel Config

All ingress rules live in one file:

```yaml
# ~/.cloudflared/config.yml
tunnel: ddaeb2d9-cb6c-4a25-8525-1f1454a80a4b
credentials-file: /home/sc/.cloudflared/ddaeb2d9-cb6c-4a25-8525-1f1454a80a4b.json

ingress:
  - hostname: hex.codeovertcp.com
    service: http://localhost:3001
  - hostname: gto-wizard.codeovertcp.com
    service: http://localhost:3000
  - hostname: wiz.codeovertcp.com
    service: http://localhost:3000
  - hostname: api.codeovertcp.com
    service: http://localhost:8642
  - hostname: ai.codeovertcp.com
    service: http://localhost:9119
  - hostname: webui.codeovertcp.com
    service: http://localhost:8787
  - hostname: space.codeovertcp.com
    service: http://localhost:8787
  - hostname: onetag.codeovertcp.com
    service: http://localhost:3031
  - service: http_status:404
```

### Port Map

| Hostname | Port | Service |
|----------|------|---------|
| `wiz.codeovertcp.com` | 3000 | GTO Wizard — Next.js frontend |
| `gto-wizard.codeovertcp.com` | 3000 | GTO Wizard — Next.js frontend |
| `hex.codeovertcp.com` | 3001 | Polytopia Clone — static serve |
| `onetag.codeovertcp.com` | 3031 | OneTag Streamlit |
| `webui.codeovertcp.com` | 8787 | Hermes WebUI |
| `space.codeovertcp.com` | 8787 | Hermes WebUI (alt) |
| `api.codeovertcp.com` | 8642 | Hermes gateway API |
| `ai.codeovertcp.com` | 9119 | Hermes dashboard |

## Services on Host

| Service | Port | Description | Systemd? |
|---------|------|-------------|----------|
| `gto-wizard-web.service` | 3000 | Next.js frontend at `~/gto-wizard-clone/apps/web` | ✅ yes |
| `gto-wizard-api.service` | 8001 | FastAPI backend at `~/gto-wizard-clone` | ✅ yes |
| `cloudflared-tunnel` | — | Single tunnel process (not systemd) | ❌ no, spawned via background |

## Key constraint
**Server-side tunnel ingress config overrides local config.** Cloudflare dashboard stores its own ingress rules. To change where a tunnel routes, update the dashboard or change the DNS CNAME. API tokens return 403 for tunnel config endpoints. The argo tunnel token (from `cert.pem`) has `tunnel:write` scope but NOT `access:edit` — you can't manage Access apps via API with it.

## Access Policy
- `wiz.codeovertcp.com` is **public** (no Cloudflare Access) — anyone can reach the app directly.
- Other domains may have Access policies requiring email OTP.

## Updating Tunnel Config

1. Edit `~/.cloudflared/config.yml` with `patch`:
   ```
   patch ~/.cloudflared/config.yml << 'EOF'
   ...old context lines...
   - hostname: wiz.codeovertcp.com
     service: http://localhost:3030  # ← old
   EOF
   ...new context lines...
   - hostname: wiz.codeovertcp.com
     service: http://localhost:3000  # ← new
   EOF
   ```
   Or use the `patch` tool with `mode=replace`.

2. Kill existing cloudflared:
   ```
   pkill -f "cloudflared tunnel"
   # wait for process to die
   ps aux | grep cloudflared | grep -v grep || echo "dead"
   ```

3. Restart in background:
   ```
   cloudflared tunnel --config /home/sc/.cloudflared/config.yml run codeovertcp >/tmp/cloudflared.log 2>&1
   ```
   Use `terminal(background=true)` — no trailing `&`.

4. Wait ~5s for QUIC connections, then verify:
   ```
   curl -s -o /dev/null -w "HTTP %{http_code} in %{time_total}s" https://wiz.codeovertcp.com/
   ```
   Expected: `HTTP 200 in 0.1s`

5. Check the tunnel is running:
   ```
   ps aux | grep cloudflared | grep -v grep
   tail -5 /tmp/cloudflared.log  # should show "Registered tunnel connection"
   ```

### Pitfall: Old cloudflared PIDs linger
After `pkill`, a stale PID may still show. Kill it explicitly with `kill -9 <PID>`. Two PIDs may appear — one is the wrapper bash process, one is the real cloudflared. Only the real one matters.

### Pitfall: Tunnel config change doesn't take effect until restart
Unlike nginx, cloudflared does NOT reload config on HUP. You must kill and restart.

### Pitfall: Wrong port = 502
If the tunnel routes to a port with nothing listening (`curl -s -o /dev/null -w "%{http_code}" http://localhost:PORT/` returns `000`), the tunnel returns HTTP 502. Always verify the local port first before blaming the tunnel.

## Verification
```bash
# Public endpoints
curl -s -o /dev/null -w 'HTTP %{http_code} in %{time_total}s' https://wiz.codeovertcp.com/

# Local health
curl -s http://localhost:3000/api/v1/health

# Tunnel status
tail -3 /tmp/cloudflared.log
```

## Logs
- Tunnel output: `/tmp/cloudflared.log` (restarted on each reboot/process restart — ephemeral)
- GTO deploy log: `~/.hermes/logs/gto-wizard-deploy.log` (rotated daily at 06:00 via cron job)

## Reference Files

- `references/hwc-deployment.md` — HWC systemd service details, binary quirks, WorkingDirectory requirement, endpoint map, and tunnel creation steps.
- `references/tunnel-config-update.md` — Step-by-step tunnel config update + restart workflow with pitfalls.
