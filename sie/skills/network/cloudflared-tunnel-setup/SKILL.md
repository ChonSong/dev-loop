---
name: cloudflared-tunnel-setup
category: network
description: A class-level skill for configuring, debugging, and managing Cloudflared tunnels — covers both basic-auth (SSL-backed) tunnels for services like onetag.codeovertcp.com and API-managed Argo tunnels with remote ingress configuration (e.g., gto-wizard). Includes debugging for API-config-overrides-local-YAML, HTTP status code interpretation, and host-vs-container routing.
---

# Cloudflared Tunnel Setup with Secure Credentials

## Overview
A class-level skill for configuring persistent Cloudflared tunnels with secure authentication. Designed for onetag.codeovertcp.com deployment with proper credential management and verification steps.

## Quick Tunnel (trycloudflare — No API Auth Needed)

When no valid Cloudflare API token is available, use the ephemeral quick tunnel. URL changes on restart.

```bash
# Start quick tunnel (no config, no creds needed — foreground)
cloudflared tunnel --url http://localhost:3005

# Or as systemd user service (persistent across reboots)
cat > ~/.config/systemd/user/cloudflared-myservice.service << 'SERVICEEOF'
[Unit]
Description=Cloudflare Tunnel for myservice
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/path/to/cloudflared --no-autoupdate tunnel --url http://localhost:3005
Restart=always
RestartSec=5
StandardOutput=append:/home/sean/.hermes/logs/cloudflared-myservice.log
StandardError=append:/home/sean/.hermes/logs/cloudflared-myservice.log

[Install]
WantedBy=default.target
SERVICEEOF

systemctl --user daemon-reload
systemctl --user enable cloudflared-myservice.service
systemctl --user start cloudflared-myservice.service
```

### Extract URL from Logs

The quick tunnel URL is logged to stdout on startup. Extract it to a known file:

```bash
# Extract URL from log
grep -oP 'https://[\w-]+\.trycloudflare\.com' /path/to/cloudflared.log | tail -1

# Or as a reusable script (save as ~/.hermes/bin/tunnel-url.sh)
cat > ~/.hermes/bin/tunnel-url.sh << 'SCRIPTEOF'
#!/bin/bash
grep -oP 'https://[\w-]+\.trycloudflare\.com' "$1" | tail -1
SCRIPTEOF
chmod +x ~/.hermes/bin/tunnel-url.sh

# Usage
~/.hermes/bin/tunnel-url.sh ~/.hermes/logs/cloudflared-myservice.log > ~/.hermes/tunnel-url.txt
```

### Note: Quick Tunnel vs Named Tunnel

| Aspect | Quick Tunnel (--url) | Named Tunnel (config.yml) |
|--------|---------------------|--------------------------|
| Auth required | None (ephemeral) | API token or origin cert |
| URL | Random trycloudflare.com | Custom hostname (DNS) |
| Persistence | Changes on restart | Stable |
| Best for | Quick access, testing | Production |
| Upgrade path | Replace with named tunnel when API token is available | API token needs `Zone:DNS:Edit + Account:Tunnel:Write` scope |

## Systemd User Service Pattern

All tunnels on the EndeavourOS host use systemd user services (`~/.config/systemd/user/`):

```bash
# Location
~/.config/systemd/user/cloudflared-<name>.service

# Enable lingering for user services (must be done once)
sudo loginctl enable-linger sean

# Commands
systemctl --user daemon-reload
systemctl --user enable cloudflared-<name>.service
systemctl --user start cloudflared-<name>.service
systemctl --user status cloudflared-<name>.service
systemctl --user stop cloudflared-<name>.service
journalctl --user -u cloudflared-<name>.service -n 50 --no-pager
```

### Existing Tunnel Services on This Host

| Service | Type | Target | Port |
|---------|------|--------|------|
| `cloudflared-hermes-webui.service` | Named + `--url` | hermes-webui (container) | 172.19.0.2:8787 |
| `cloudflared-onetag.service` | Named + `--url` | onetag (streamlit) | localhost:8502 |
| `cloudflared-hwc.service` | Quick tunnel (no auth) | HWC | localhost:3005 |
| `agent-os-cloudflared` (Docker) | Argo token via Docker | agent-os backend | backend:3001 |

## Implementation Steps
1. **Create Secure Credentials File**
   ```bash
   cat > /home/hermeswebui/.hermes/cloudflared/onetag-creds.json <<EOF
   {
     "username": "sa",
     "password": "dawnofdarren"
   }
   EOF
   ```
2. **Update Tunnel Configuration**
   ```yaml
   # /home/hermeswebui/.hermes/cloudflared/onetag-config.yml
   tunnel: b3200be4-a8a8-4381-980b-038e402d8702
   credentials-file: /home/hermeswebui/.hermes/cloudflared/onetag-creds.json
   ingress:
     - hostname: onetag.codeovertcp.com
       service: http://localhost:8501
   ```
3. **Verify Service Availability**
   Confirm a service is running on `localhost:8501` (e.g., `ss -tlnp | grep 8501`).
4. **Start Tunnel**
   ```bash
   nohup /home/hermeswebui/.hermes/bin/cloudflared --config /home/hermeswebui/.hermes/cloudflared/onetag-config.yml run > /home/hermeswebui/.hermes/logs/onetag-tunnel.log 2>&1 &
   ```
5. **Validate Status**
   ```bash
   /home/hermeswebui/.hermes/bin/cloudflared tunnel --config /home/hermeswebui/.hermes/cloudflared/onetag-config.yml tunnel-status
   ```

## Common Pitfalls
- ❌ Incorrect `credentials-file` path
- ❌ Service not running on target port
- ❌ Tunnel ID mismatch in config
- ❌ Insufficient file permissions
- ❌ **API config overrides local YAML**: Cloudflare Argo tunnels fetch ingress rules from the API at startup. `PUT /accounts/{id}/cfd_tunnel/{id}/configurations` overrides whatever is in your local YAML. Always update the API config, not just the file.
- ❌ **localhost from host misses container**: With `network_mode: host`, container ports are NOT accessible at host `localhost`. Use the container's Docker bridge IP (e.g. `172.19.0.2`) in the ingress `service` field.
- ❌ **DNS CNAME update lies**: Cloudflare may return `success: true` on a DNS PUT but keep the old value. Always verify with a separate GET after updating.
- ❌ **Tunnel ID as last arg to `run`**: When using `--credentials-file` without a config file, the tunnel ID must be passed as the last argument: `cloudflared tunnel --credentials-file creds.json run <tunnel-id>`.
- ❌ **CNAME must use tunnel UUID, not tunnel name**: DNS CNAME for a tunnel-routed domain MUST point to `{tunnel-uuid}.cfargotunnel.com`, NOT `{tunnel-name}.cfargotunnel.com`. Using the human-friendly name returns HTTP 530 / error code 1033 because Cloudflare's edge can't resolve the named tunnel to connections. Check existing working records (e.g. `hex.codeovertcp.com -> ddaeb2d9-....cfargotunnel.com`) for the canonical pattern.
- ❌ **Stale cloudflared PID survives restart**: The wrapper shell script (`bash -lic cloudflared tunnel ... > log 2>&1`) persists the parent PID even after the child cloudflared is killed. After restart, verify with `ps aux | grep cloudflared | grep -v grep` and `kill -9` any remaining wrapper PIDs.
- ❌ **SIGHUP won't register new hostnames**: `kill -HUP <pid>` reloads config but does NOT register new ingress hostnames with the Cloudflare edge. Previously-unrouted hostnames need a full tunnel kill+restart. SIGHUP only works for changes to existing ingress rules (different port-to-service mapping).

## Domain-Not-Reachable Diagnostic Workflow

When a user reports "X.codeovertcp.com is down", follow this sequence:

1. **Check DNS resolution** — does the domain resolve?
   ```bash
   dig +short X.codeovertcp.com
   ```
   Cloudflare-proxied domains return Cloudflare edge IPs (172.67.x.x, 104.21.x.x). If it returns nothing or a raw IP, the DNS record is missing or proxying is off.

2. **Check the tunnel ingress config** — is the hostname listed?
   ```bash
   cat /home/sc/.cloudflared/config.yml | grep -A1 X.codeovertcp.com
   ```
   If missing, the tunnel doesn't know where to route traffic for that domain.

3. **Check the backend service** — is it actually running?
   ```bash
   curl -sI http://localhost:$PORT
   ```
   If the backend is down, fix that first — no tunnel config will help.

4. **Add missing hostname to tunnel config**:
   Edit `/home/sc/.cloudflared/config.yml` and add an ingress entry:
   ```yaml
   - hostname: X.codeovertcp.com
     service: http://localhost:$PORT
   ```
   Insert it in alphabetical/hostname order among existing ingress rules, before the catch-all `- service: http_status:404`.

5. **Reload cloudflared** — SIGHUP hot-reloads config:
   ```bash
   kill -HUP $(pgrep -f "cloudflared tunnel.*config")
   ```
   This avoids restart and is preferred when the tunnel is serving other domains. If the process crashes on reload, restart it normally:
   ```bash
   /usr/local/bin/cloudflared tunnel --config /home/sc/.cloudflared/config.yml run codeovertcp
   ```

6. **Verify** — traffic now reaches the backend:
   ```bash
   curl -s -o /dev/null -w "HTTP %{http_code}" https://X.codeovertcp.com
   ```
   A 302/307 means Cloudflare Access is interposing (expected for Access-protected sites — the tunnel is working). A 200/404 means the backend is responding.

## HTTP Status Code Quick Reference
| Code | Meaning | Likely Cause |
|------|---------|-------------|
| 530 | Origin unreachable | DNS points to wrong tunnel, or tunnel not receiving traffic |
| 502 | Bad Gateway | Tunnel connected but origin unreachable from tunnel client |
| 503 | No ingress | Tunnel running but no ingress rules configured |
| 404 | Not Found | Tunnel working, app returns 404 |
| 302 | Redirect (Cloudflare Access) | **Expected** — Cloudflare Access auth challenge. Tunnel is working, user needs to authenticate. |
| 307 | Redirect | Tunnel working, app redirecting (common for / → /gto/equity) |

## Support Files

- `references/cloudflared-tunnel-setup.md` — Consolidated tunnel setup reference
- `references/onetag-creds-setup-detail.md` — Detailed credential file format and permissions
- `references/gto-wizard-tunnel-debugging.md` — GTO Wizard tunnel debugging notes (API config override, HTTP status codes, host-vs-container routing)
- `references/shared-browser-via-cdp-tunnel.md` — Shared browser setup using Chrome CDP + Node.js viewer + tunnel (co-browsing pattern)
- `scripts/setup-onetag-tunnel.sh` — Automated credential + config creation script (creates dirs, writes creds with 600 perms, generates config template)

## Maintenance Schedule

| Frequency | Task | Command |
|-----------|------|---------|
| Daily | Verify tunnel status | `cloudflared tunnel list` |
| Weekly | Backup credentials | `zip credentials-backup-$(date +%Y%m%d).zip ~/.hermes/cloudflared/onetag-creds.json` |
| Monthly | Rotate credentials | Update `onetag-creds.json` and restart tunnel |

## Best Practices
- Store credentials in dedicated JSON file with strict permissions (`chmod 600`)
- Monitor logs at `/home/hermeswebui/.hermes/logs/onetag-tunnel.log`
- Rotate credentials periodically