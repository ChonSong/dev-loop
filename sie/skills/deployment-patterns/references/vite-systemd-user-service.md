# Vite Static Preview as Systemd User Service

## Unit File

```ini
[Unit]
Description=Static App Server
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/sc/repos/my-project
ExecStart=/home/sc/.hermes/node/bin/npx vite preview --port 3001 --host
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
```

Place at `~/.config/systemd/user/<name>.service`.

## Key Points

| Rule | Why |
|------|-----|
| **Omit `User=`** | User-scoped units already run as the owning user. `User=sc` causes `Failed at step GROUP spawning: Operation not permitted` |
| **Absolute npx path** | systemd user units don't inherit the user's PATH. Use the hermetic Node found at `~/.hermes/node/bin/` (checked in memory/scripts) |
| **WorkingDirectory required** | Vite resolves its config relative to CWD. Without it, `vite preview` fails to find vite.config.ts |
| **Port conflict** | If port 3001 is in use, Vite auto-selects another — breaks tunnel ingress. Kill stale processes: `pkill -f "vite preview"` before restart |
| **Restart vs tunnel** | The no-agent deploy watchdog can auto-restart if the server dies, or pair with `Restart=always` in the unit |

## Setup

```bash
mkdir -p ~/.config/systemd/user
# write unit file to ~/.config/systemd/user/<name>.service

systemctl --user daemon-reload
systemctl --user enable --now <name>.service

# Verify
systemctl --user status <name>.service --no-pager
curl -s -o /dev/null -w "%{http_code}" http://localhost:3001/
```

## Removal

```bash
systemctl --user stop <name>.service
systemctl --user disable <name>.service
rm ~/.config/systemd/user/<name>.service
systemctl --user daemon-reload
```
