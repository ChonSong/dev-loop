# Hermes Agent — Complete State Backup & Container Docs

Automated backup of Hermes Agent state to GitHub. Runs every 6 hours via host cron.

## What's Synced (every 6h)

| Item | Description |
|------|-------------|
| `config.yaml`, `SOUL.md`, `auth.json`, `kanban.db` | Core state |
| `state.db.gz` | Compressed SQLite DB (all sessions, messages, tokens) — 269MB → 94MB |
| `skills/` | All skill definitions and references |
| `memory/` | MEMORY.md and USER.md |
| `sessions/` | Session JSON transcripts |
| `cron/` | Cron job definitions and output logs |
| `scripts/` | Sync and utility scripts |
| `plans/`, `workspace/`, `hooks/` | Plans, workspace files, hooks |
| `secrets/.env` | API keys |

## Recovery (Bare Machine)

```bash
# 1. Clone
git clone https://github.com/ChonSong/hermes-sync.git ~/hermes-recovery

# 2. Decompress state DB
gunzip ~/hermes-recovery/state.db.gz

# 3. Copy to hermes data dir
cp ~/hermes-recovery/config.yaml ~/.hermes/
cp ~/hermes-recovery/state.db ~/.hermes/
cp -r ~/hermes-recovery/skills ~/.hermes/
cp -r ~/hermes-recovery/memory ~/.hermes/
cp -r ~/hermes-recovery/sessions ~/.hermes/
cp -r ~/hermes-recovery/cron ~/.hermes/
cp -r ~/hermes-recovery/secrets/.env ~/.hermes/.env

# 4. Start container
docker run -v ~/.hermes:/opt/data ghcr.io/chonsong/hermes-sync:latest
```

---

## Container Architecture

**Image**: `hermes-sync:latest` (based on Hermes Agent v0.13.0, 2026.5.7)

### Services

| Service | Port | URL | Status Check |
|---------|------|-----|--------------|
| Gateway API | 8642 | http://localhost:8642/health | `curl -s localhost:8642/health` |
| Dashboard | 9119 | http://localhost:9119/ | `curl -s localhost:9119/` |

### Docker Compose

Located at `~/hermes-sync/docker/docker-compose.yml`:

```yaml
services:
  gateway:
    image: hermes-sync:latest
    container_name: hermes
    restart: unless-stopped
    network_mode: host
    volumes:
      - /home/sean/.hermes:/opt/data
      - /home/sean/hermes-sync:/opt/data/hermes-sync:ro
      - /home/sean/Downloads:/home/sean/Downloads:ro
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - HERMES_UID=1000
      - HERMES_GID=1001
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8642/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    command: ["gateway", "run"]

  dashboard:
    image: hermes-sync:latest
    container_name: hermes-dashboard
    restart: unless-stopped
    network_mode: host
    depends_on:
      gateway:
        condition: service_healthy
    volumes:
      - /home/sean/.hermes:/opt/data
      - /home/sean/hermes-sync:/opt/data/hermes-sync:ro
      - /home/sean/Downloads:/home/sean/Downloads:ro
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - HERMES_UID=1000
      - HERMES_GID=1001
    command: ["dashboard", "--host", "127.0.0.1", "--no-open"]
```

### Quick Commands

```bash
# Status / logs
docker ps | grep hermes
docker logs hermes

# Restart
cd ~/hermes-sync/docker && docker-compose restart

# TUI (from real terminal)
docker exec -it hermes /opt/hermes/.venv/bin/hermes --tui
docker exec -it hermes /opt/hermes/.venv/bin/hermes --tui --resume SESSION_ID

# SSH to host from container (port 22 or 2229)
docker exec hermes ssh -i /opt/data/container_key -o StrictHostKeyChecking=no sean@localhost
```

### SSH Access

Container → host SSH via `/opt/data/container_key`. Key persisted at `/opt/data/container_key` (volume mount).

```bash
# From container
docker exec hermes ssh -i /opt/data/container_key -o StrictHostKeyChecking=no sean@localhost

# From container (via container→host SSH)
ssh -i /opt/data/container_key -o StrictHostKeyChecking=no sean@localhost
```

### Image Management

```bash
docker images hermes-sync:latest
docker tag hermes-sync:latest ghcr.io/chonsong/hermes-sync:v0.13.0
docker push ghcr.io/chonsong/hermes-sync:v0.13.0
cd ~/hermes-sync/docker && docker build -t hermes-sync:latest -f Dockerfile .
```

---

## Sync Mechanism

- **Schedule**: Host cron `0 */6 * * *` → `/home/sean/.hermes/scripts/sync-cron.sh` → `hermes-sync-backup.py`
- **Independence**: Runs entirely on host — no container dependency
- **Working repo**: `/home/sean/.hermes/cache/sync-work/hermes-sync/`
- **GitHub**: `ChonSong/hermes-sync` (private)

### How it works
1. Cron triggers `sync-cron.sh`
2. Script fixes permissions (container writes files as root)
3. Python script clones/pulls repo, copies all state files
4. Compresses `state.db` → `state.db.gz` (269MB → 94MB)
5. Commits and pushes with timestamp message

### Important: Container writes as root

The Hermes container runs as root inside, so new files (sessions, skills updates) are owned by root. The sync cron script runs `chmod -R a+r` before each sync to ensure the host user `sean` can read and commit them.

If sync fails with `Permission denied`, run:
```bash
docker run --rm --privileged --pid=host --network=host -v /:/host alpine:latest \
  sh -c 'chown -R 1000:1000 /host/home/sean/.hermes/ && echo DONE'
```

---

## Troubleshooting

### Container won't start
```bash
docker ps -a | grep hermes
docker logs hermes --tail 100
cd ~/hermes-sync/docker && docker-compose down && docker-compose up -d
```

### TUI shows "gateway exited"
```bash
docker exec hermes pkill -9 -f tui_gateway
docker exec hermes pkill -9 -f 'hermes.*tui'
docker exec hermes ls /opt/hermes/tui_gateway/
cd ~/hermes-sync/docker && docker-compose restart
```

### API not responding
```bash
curl -s localhost:8642/health
docker exec hermes ps aux | grep gateway
docker exec hermes /opt/hermes/.venv/bin/hermes gateway restart
```

### Permission denied errors
```bash
chmod 644 /home/sean/.hermes/cron/jobs.json
chmod 600 /opt/data/container_key
```

### Sync fails
```bash
# Manual run
HERMES_HOME=/home/sean/.hermes python3 /home/sean/.hermes/scripts/hermes-sync-backup.py

# Check logs
cat /home/sean/.hermes/logs/sync-backup.log
```

---

## Known Issues (Fixed)

1. **Missing tui_gateway/** — Fixed: Added `COPY tui_gateway/ /opt/hermes/tui_gateway/` to Dockerfile
2. **Missing model_tools.py** — Fixed: Added `COPY model_tools.py /opt/hermes/model_tools.py`
3. **@hermes/ink missing dist/** — Fixed: Copy from `packages/hermes-ink` instead of `node_modules/@hermes/ink`
4. **Zombie processes** — Fixed: Kill before restart
5. **Cron permission race** — Cosmetic, doesn't affect functionality
6. **state.db >100MB GitHub limit** — Fixed: gzip compression (269MB → 94MB)
7. **Container writes as root** — Fixed: sync-cron.sh does chmod before copy

## File Locations

| File | Location | Description |
|------|----------|-------------|
| Docker config | `~/hermes-sync/docker/Dockerfile` | Multi-stage build |
| Docker compose | `~/hermes-sync/docker/docker-compose.yml` | Container orchestration |
| SSH key | `/opt/data/container_key` | Container→host auth |
| Sessions | `/home/sean/.hermes/sessions/` | Session history |
| Memory | `/home/sean/.hermes/memory/` | Agent memory |
| Config | `/home/sean/.hermes/config.yaml` | Main config |
| Sync script | `/home/sean/.hermes/scripts/hermes-sync-backup.py` | Backup automation |
| Sync cron | `/home/sean/.hermes/scripts/sync-cron.sh` | Cron trigger |

## Notes

- Health check uses port 8642 (gateway API), not 8000
- Container runs as UID 1000 (hermes) inside, UID 1000 (sean) on host
- `${HOME}` in docker-compose resolves to `/root` — explicit paths used instead
- TUI requires actual terminal (not docker exec in non-interactive shell)
- Disk usage: ~90% (391G/461G)