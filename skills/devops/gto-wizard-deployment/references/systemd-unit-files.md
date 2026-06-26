# GTO Wizard Systemd Unit Files

Current as of June 2026. All units run as `systemctl --user` services under user `sean` on the host.

## gto-wizard-api.service

```ini
[Unit]
Description=GTO Wizard FastAPI backend
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/home/sean/gto-wizard-clone/apps/api
ExecStart=/home/sean/hermes-apps-venv/bin/uvicorn main:app --host 0.0.0.0 --port 8003 --log-level warning
Environment=PYTHONPATH=..
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
```

**python path note:** `PYTHONPATH=..` is critical — it lets `from routers import X` resolve relative to `apps/api/`.

## gto-wizard-web.service

```ini
[Unit]
Description=GTO Wizard Next.js frontend
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/home/sean/gto-wizard-clone/apps/web
Environment=PATH=/home/sean/.hermes/node/bin:/usr/local/bin:/usr/bin:/bin
Environment=NEXT_PUBLIC_API_URL=http://localhost:8003
ExecStart=/usr/bin/npx next start -p 8564
Restart=always
RestartSec=15

[Install]
WantedBy=default.target
```

**PATH note:** Must include `/home/sean/.hermes/node/bin` explicitly. The user-level PATH (as set by .bashrc) is NOT loaded by systemd --user units unless `DefaultEnvironment` is configured.

## Management Commands

```bash
# View logs
journalctl --user -u gto-wizard-api.service -n 50 --no-pager
journalctl --user -u gto-wizard-web.service -n 50 --no-pager

# Follow logs
journalctl --user -u gto-wizard-api.service -f

# Restart
systemctl --user restart gto-wizard-api.service

# Stop (tunnel won't reach it, frontend gets 502)
systemctl --user stop gto-wizard-api.service

# Disable (won't start on boot)
systemctl --user disable gto-wizard-web.service
```

## Verification

```bash
# From container
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 "
systemctl --user --no-pager status gto-wizard-api.service gto-wizard-web.service | head -10
"
```

Expected: both show `Active: active (running)`.
