# Disconnected Container: Full Diagnosis Log

**Session:** 2026-05-03, hermes-agent container running on 192.168.1.117 (hpprobook)
**Problem:** Cron job tried to deploy `agent-os` from inside hermes container — failed at every access layer

## What Worked

| Tool | Available? | Command |
|------|-----------|---------|
| Python stdlib (`urllib.request`) | ✅ | HTTP health checks without curl |
| `docker --version` | ✅ (CLI present) | Shows version 26.1.5, but daemon unreachable |
| `ssh` binary | ✅ at `/usr/bin/ssh` | But sshd not running on localhost/127.0.1.1 |
| `python3` | ✅ | Full Python available |
| `subprocess.run()` | ✅ | For any binary on PATH |

## What Was NOT Available

| Tool | Why Missing |
|------|-------------|
| `curl` | Not installed in container |
| `systemctl` | Not in container |
| `ss` / `netstat` | Not in container |
| `ping` | Not in container |
| `docker.sock` | Not mounted |
| SSH to host | sshd not running on host |
| Docker TCP (2375/2376/2377) | All closed |

## Network Topology Discovered

- Container hostname: `hpprobook` (hostname -I shows 192.168.1.117, 172.17.0.1, etc.)
- Container PID 1: `/usr/bin/tini -g -- /opt/hermes/docker/entrypoint.sh gateway run`
- This confirms we are inside hermes-agent container, not on bare metal
- The container uses `--network=host` → shares host's network namespace
- But Docker socket is NOT mounted → cannot control Docker daemon
- SSH to `localhost` (port 22) refused → sshd not running inside container
- SSH to `192.168.1.117` (port 22) refused → sshd not running on host OR not reachable

## Container Environment Variables (relevant)

```
HOME=/opt/data/home
HERMES_HOME=/opt/data
HOSTNAME not set
TERMINAL_DOCKER_IMAGE=nikolaik/python-nodejs:python3.11-nodejs20
DOCKER_HOST not set
```

## agent-os docker-compose.yml (confirmed present)

Path: `/opt/data/hermes-sync/projects/agent-os/docker-compose.yml`

```yaml
services:
  agent-os:
    image: ghcr.io/chonsong/agent-os:latest
    container_name: agent-os
    restart: unless-stopped
    environment:
      - MINIMAX_API_KEY=${MINI...KEY}
      - NANOBOT_API_URL=http://localhost:8900
      - PORT=9120
    volumes:
      - nanobot-workspace:/opt/data/home/.nanobot/workspace
      - hermes-home:/opt/data
    ports:
      - "9120:9120"
      - "8900:8900"
    healthcheck:
      test: ["CMD", "curl", "-sf", "http://localhost:9120/health"]
```

## Key Lesson

The hermes container on hpprobook is configured with `--network=host` (network shares with host) but WITHOUT the Docker socket mounted. This means:
- The container CAN reach host ports (9120, 8900) via `localhost` — IF those services run on the host
- The container CANNOT manage Docker (no socket) → cannot `docker pull`, `docker compose`, `docker ps`
- The container CANNOT SSH to host (no sshd, no keys configured)

**For agent-os deployment to work from cron inside hermes**, the docker socket must be mounted into the hermes container.
