# HWC (Hermes Web Computer) Deployment

## Systemd Service

Created 2026-06-12 at `~/.config/systemd/user/hwc-server.service`:

```
[Unit]
Description=Hermes Web Computer — Go backend + Svelte 5 frontend
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/home/sean/.hermes/hermes-web-computer/frontend
ExecStart=/home/sean/.hermes/hermes-web-computer/agent-os
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
```

## Critical Quirk: WorkingDirectory

The HWC Go binary resolves its frontend dist path from the **working directory**, checking these paths in order:

1. `./frontend/dist` (relative to cwd)
2. `/opt/data/hermes-web-computer/frontend/dist` (absolute)
3. `../frontend/dist` (one level up)
4. `../../frontend/dist` (two levels up)

When started from the repo root (`/home/sean/.hermes/hermes-web-computer`), path #1 (`./frontend/dist`) should exist but may silently fail. The reliably working path is to set `WorkingDirectory` to `frontend/` so that path #3 (`../frontend/dist`) resolves correctly.

**DO NOT** set `WorkingDirectory=/home/sean/.hermes/hermes-web-computer` — the SPA (index.html) will return 404. Always use `frontend/`.

## API Endpoints

| Path | Type | Response |
|------|------|----------|
| `/` | HTTP GET | Svelte 5 SPA (title: "Hermes Web Computer") |
| `/health` | HTTP GET | `ok` |
| `/ws` | WebSocket | Multiplexer for tiling WM, pty, file system, docker, chat |

## Binary Info

- Location: `~/hermes-web-computer/agent-os`
- Size: ~14MB ELF (Go 1.26, statically linked)
- Version: v1.0.0 (from `package.json`)
- Build date: last `git log` commit date or `stat` Modify time
- Memory: ~3.4MB RSS (peak ~4.1MB)

## Adding a HWC Cloudflare Tunnel

If you want to expose HWC at a subdomain (e.g., `hwc.codeovertcp.com`):

1. Create a new tunnel or reuse an existing one
2. Add ingress rule pointing to `localhost:3005`
3. Create DNS CNAME to the tunnel ID
4. Create systemd service: `cloudflared-hwc.service` (model after `cloudflared-gto-wizard.service`)
5. Enable: `systemctl --user enable --now cloudflared-hwc.service`

## Verification

```bash
# From host:
curl -s http://localhost:3005/health          # → ok
curl -s -o /dev/null -w "%{http_code}" http://localhost:3005/  # → 200
curl -s http://localhost:3005/ | grep -o '<title>[^<]*</title>'  # → Hermes Web Computer

# From container (if on same Docker network):
curl -s http://172.19.0.1:3005/health
```
