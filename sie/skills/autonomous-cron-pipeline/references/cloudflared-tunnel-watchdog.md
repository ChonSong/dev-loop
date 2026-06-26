# Cloudflared Tunnel Watchdog — Paths and Fixes

## Watchdog Script Location
`/home/hermeswebui/.hermes/scripts/hermes-webui-tunnel-watchdog.sh`

## Systemd Service
`hermes-webui-tunnel.service` (user systemd) — status: `systemctl --user status hermes-webui-tunnel.service`

## Cloudflared Binary
| Location | Purpose |
|----------|---------|
| `/home/sean/.hermes/bin/cloudflared` | Source (original) |
| `/tmp/cloudflared` | Working copy used by systemd service |

The service has `ExecStart=/tmp/cloudflared tunnel run ...`. If `/tmp/cloudflared` is missing, the service fails silently. Fix:
```bash
cp /home/sean/.hermes/bin/cloudflared /tmp/cloudflared && chmod +x /tmp/cloudflared
systemctl --user daemon-reload
systemctl --user start hermes-webui-tunnel
```

## Credential Files
| Path | State |
|------|-------|
| `/home/sean/.cloudflared/hermes-webui-creds.json` | ✅ Valid (TunnelID: `bf723d4c-7299-4a6b-a2f9-6cee6bec86dc`) |
| `/home/sean/.cloudflared/hermes-webui-argo-token.txt` | ✅ Valid (245 bytes, JWT format) |
| `/opt/data/cloudflared/hermes-webui-creds.json` | ❌ Corrupt — this is a directory, not a file |

**Note:** The watchdog script defaults to `CRED_FILE="/home/sean/.cloudflared/hermes-webui-creds.json"` which is correct. If the token approach is needed instead, the argo-token file is the fallback.

## Watchdog Script Pattern
The watchdog script checks if the tunnel is alive and restarts it if needed. Key variables:
- `CLOUDFLARED="${CLOUDFLARED:-/tmp/cloudflared}"` — env-var override
- `CRED_FILE="/home/sean/.cloudflared/hermes-webui-creds.json"`
- `LOG="${HERMES_LOGDIR:-/home/hermeswebui/.hermes/logs}/hermes-webui-tunnel.log"`
- Tunnel name: `hermes-webui`
- Local target: `http://172.19.0.2:8787`
- Container IP: `172.19.0.2` (backend), host: `172.19.0.1`

## Cron Job
Watchdog cron job ID: `e751d8b54eb5`
- Schedule: `*/5 * * * *` (every 5 minutes)
- Workdir: `/home/hermeswebui/.hermes`
- Repeat: `forever`
- Old broken job: `356d146923b1` (removed, had wrong script path)

## "Invalid tunnel secret" — Normal Behavior
This error in `journalctl --user -u hermes-webui-tunnel` is **not a failure**. Random public IPs hit Cloudflare's edge and get rejected. Verify tunnel health:
```bash
curl http://localhost:8787/  # should return HTML
```
If this returns HTML, the tunnel is working correctly.

## Tunnel URLs
- Local: `http://localhost:8787/`
- Cloudflare: `https://hermes-webui.trycloudflare.com/` (verified working 2026-05-25)
- Second tunnel (agent-os): separate PID 1649, routes `backend:3001`