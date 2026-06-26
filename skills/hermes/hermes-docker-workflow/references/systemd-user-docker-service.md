# systemd User Service for Docker Compose (Pattern)

## The Core Problem

`docker compose up -d` exits quickly (container keeps running in background). systemd's default `Type=simple` expects the process to keep running — so it marks the service as "failed" the moment the command exits.

## The Solution: Type=oneshot + RemainAfterExit

```ini
[Unit]
Description=My Docker Service
After=network.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=%h/path/to/project
ExecStart=/usr/bin/docker compose -f %h/path/to/docker-compose.yml up -d
ExecStop=/usr/bin/docker compose -f %h/path/to/docker-compose.yml down
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

## Why This Works

| Flag | Effect |
|------|--------|
| `Type=oneshot` | The service runs once and is considered complete when ExecStart exits |
| `RemainAfterExit=yes` | systemd marks the service as "active" even after ExecStart exits |
| `ExecStop` | Runs when service is stopped (via `systemctl stop` or reboot) |
| `Restart=on-failure` | Restarts ExecStart if the container dies unexpectedly |

## Enabling at Boot (Linger)

User services don't auto-start at boot unless the user is logged in. Enable linger:

```bash
loginctl enable-linger sean
```

This allows user services to start at boot without anyone logging in.

## Key Restrictions

- **No `Requires=docker.service`**: User-level systemd cannot track system Docker daemon as a dependency. Docker must already be running.
- **No `After=docker.service`**: Same reason — user services can't depend on system services this way.
- **Paths use `%h`**: The home directory placeholder ensures paths resolve correctly regardless of the user's home location.

## Verify It's Working

```bash
# Check service status
systemctl --user status myservice.service

# Should show: Active: active (exited)
# The container should still be running:
docker ps | grep myservice

# Check if it will start on boot
systemctl --user list-unit-files | grep myservice
# Should show: myservice.service enabled
```

## When It Won't Start

```bash
# 1. Check logs
journalctl --user -u myservice.service -n 50

# 2. Manually verify compose works
cd ~/.config/myproject
docker compose up -d

# 3. Check container is healthy
docker ps --format '{{.Names}} {{.Status}}'
```