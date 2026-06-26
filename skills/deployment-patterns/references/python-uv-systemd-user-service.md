# Python/UV App → systemd --user Service

Deploy a Python application managed by `uv` as a user-level systemd service. Use this when `sudo` is unavailable for system-level units, or you want per-user process management.

## When to Use

- Host has no Docker and no sudo, but `systemctl --user` works
- Python app uses `uv` for dependency management
- You want auto-start on login, auto-restart on failure, and log management

## Quickstart

### 1. Service Unit

Write to `~/.config/systemd/user/<service-name>.service`:

```ini
[Unit]
Description=My Python Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=%h/repos/my-project/.venv/bin/python -m my_package.cli serve
WorkingDirectory=%h/repos/my-project
Restart=on-failure
RestartSec=5
Environment=PORT=8000
Environment=LOG_LEVEL=info

[Install]
WantedBy=default.target
```

Key points:
- `%h` expands to the user's home directory (`$HOME`)
- Point `ExecStart` to `.venv/bin/python` (not system Python) to use `uv`-managed deps
- `WorkingDirectory` must be repo root so relative paths (`config.yaml`, `app.db`) resolve
- `Environment=` lines for config that would otherwise be in a `.env`

### 2. Enable & Start

```bash
mkdir -p ~/.config/systemd/user

# Write the unit file
cat > ~/.config/systemd/user/energy-router.service << 'UNIT'
[Unit]
...
UNIT

# Reload, enable, start
systemctl --user daemon-reload
systemctl --user enable my-service.service
systemctl --user start my-service.service

# Verify
systemctl --user status my-service.service --no-pager
curl -s http://localhost:8000/health
```

### 3. Ensure Linger (Boot Start)

If the user never logs in interactively (e.g. headless server), enable linger so services start at boot:

```bash
sudo loginctl enable-linger sc
```

Check: `loginctl show-user sc | grep Linger` → `Linger=yes`

## Adapting from System-Level to User-Level

Existing deploy scripts often target `/etc/systemd/system/`. When they need `sudo`:

| System-level | User-level |
|-------------|------------|
| `/etc/systemd/system/my.service` | `~/.config/systemd/user/my.service` |
| `ExecStart` with absolute paths | `ExecStart` with `%h/` or relative paths |
| `User=` directive | Not needed — runs as current user |
| `sudo systemctl` | `systemctl --user` |
| Group `WantedBy=multi-user.target` | `WantedBy=default.target` |

### Transform Script

When the project has a `deploy/energy-router.service` targeting system-level:

```bash
mkdir -p ~/.config/systemd/user
# Read the system-level unit, strip User=, fix paths
sed 's|ExecStart=/usr/bin/python3|ExecStart=%h/repos/project/.venv/bin/python|' deploy/energy-router.service \
  | sed 's|WorkingDirectory=/opt|WorkingDirectory=%h/repos/project|' \
  | sed '/^User=/d' \
  | sed 's|WantedBy=multi-user.target|WantedBy=default.target|' \
  > ~/.config/systemd/user/project.service
```

## Verifying the Running Service

```bash
# Status and logs
systemctl --user status my-service --no-pager
journalctl --user -u my-service --no-pager -n 30

# Health endpoint
curl -s http://localhost:8000/health
curl -s http://localhost:8000/livez
curl -s http://localhost:8000/readyz

# Metrics (if Prometheus endpoint)
curl -s http://localhost:8000/metrics | head -20
```

## Restart Flow (After Code Changes)

```bash
cd ~/repos/my-project
git pull

# If deps changed
uv sync

# Restart
systemctl --user restart my-service

# Verify
sleep 2 && curl -s http://localhost:8000/health
```

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `Failed to connect to bus: No such file or directory` | No D-Bus session (e.g. inside container) | Install `dbus-user-session`, run `systemctl --user daemon-reload` from a real login shell |
| Service starts then immediately exits with `code=exited` | `ExecStart` path wrong or module not found | `systemctl --user cat my-service` to verify path, then run the `ExecStart` command directly to test |
| `WorkingDirectory` resolves to wrong location | `%h` expansion or tilde issue | Use absolute paths: `/home/sc/repos/project` |
| Port already in use | Another process on that port | `ss -tlnp \| grep :PORT` to find it |
| Python can't find module | Venv not activated in `ExecStart` | Always use `.venv/bin/python -m module.path` — never just `python` or `uv run` |
| `systemctl cat my-service` returns "No files found" | Service may be user-level, not system-level | Always check both: `systemctl cat my-service` AND `systemctl --user cat my-service`. User-level units live in `~/.config/systemd/user/` — invisible to the system-level `systemctl` command. |
| `systemctl --user status` shows "Failed to connect to bus" | No D-Bus session (common in containers or non-login shells) | Install `dbus-user-session`, run from a real login shell, or set `DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus`
