# Container Debugging — Hermes Agent in Docker

## Finding the Container Name

```bash
docker ps -a --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"
```

Common names: `hermes`, `hermes-agent`, `hermes-dashboard`. The running session is typically the one with recent uptime.

## Finding the Hermes Binary Inside the Container

The path varies by installation. Use `find`:

```bash
docker exec <container_name> find / -name "hermes" -type f 2>/dev/null | head -20
```

Expected paths on a source-installed hermes-agent:
- `/opt/hermes/.venv/bin/hermes`
- `/opt/hermes/hermes`
- `/opt/data/hermes-agent/hermes`

## Fixing Terminal (Broken CWD)

**Symptom:** `FileNotFoundError: /home/sean/workspace` on every terminal call.

**Cause:** `terminal.cwd` in config.yaml points to a path that doesn't exist inside the container.

**Fix sequence:**

```bash
# 1. Find the binary
docker exec <container_name> find / -name "hermes" -type f 2>/dev/null

# 2. Set the correct cwd (use the path found above)
docker exec <container_name> /opt/hermes/.venv/bin/hermes config set terminal.cwd /opt/data

# 3. Reset the session — REQUIRED for config change to take effect
# In the Hermes session: /reset
# Or: docker restart <container_name>
```

After reset, verify with:
```bash
docker exec <container_name> /opt/hermes/.venv/bin/hermes config | grep terminal.cwd
```

## Common Container Names vs Reality

| Assumed Name | Actual Name | Notes |
|-------------|-------------|-------|
| `hermes-agent` | `hermes` | Most common |
| `hermes-agent` | `hermes-dashboard` | Second instance |
| `hermes-agent` | varies | Always check `docker ps -a` |

## Verified Working Patterns

```bash
# Check config
docker exec hermes /opt/hermes/.venv/bin/hermes config edit

# Check version
docker exec hermes /opt/hermes/.venv/bin/hermes --version

# Health check
docker exec hermes /opt/hermes/.venv/bin/hermes doctor

# List cron jobs
docker exec hermes /opt/hermes/.venv/bin/hermes cron list
```

## Entrypoint Bypass Warning

Using `sleep infinity` or a command on PATH as the container CMD bypasses the entrypoint script. The entrypoint only runs when you invoke `hermes` (not found on PATH) or pass a non-Path command:

```bash
# This RUNS the entrypoint ✓
docker run hermes-agent hermes --version

# This BYPASSES the entrypoint ✗
docker run hermes-agent sleep infinity
```

If you need entrypoint + persistent container, set `HERMES_HOME`, `HERMES_UID`, `HERMES_GID` env vars and use `docker exec`.

## Volume Mount Reference

From `hermes-sync/docker/docker-compose.yml`:

| Host Path | Container Path | Purpose |
|-----------|---------------|---------|
| `~/.hermes` | `/opt/data` | Config, secrets, skills, sessions, logs |
| `~/.hermes-sync` | `/opt/data/hermes-sync:ro` | Sync repo (read-only) |
| `~/Downloads` | `/home/sean/Downloads` | Downloads |
| `/var/run/docker.sock` | `/var/run/docker.sock` | Docker CLI |

**`/home/sean/workspace` is NOT mounted** — never set `terminal.cwd` to a host path.
