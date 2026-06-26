# hermes-webui: Port 8787 Recovery & Persistence

## Quick Status Check

```bash
# From host — check if hermes-webui is running
docker ps --format '{{.Names}} {{.Status}}' | grep hermes-webui
curl -s -o /dev/null -w 'HTTP:%{http_code}' http://127.0.0.1:8787/

# Or via ctl.sh (if running native python)
~/.hermes/hermes-webui/ctl.sh status
tail -30 ~/.hermes/webui.log
```

## Common Failure: Broken `.venv` (Missing pip)

**Symptom**: `bootstrap.py` fails with:
```
[bootstrap] Installing WebUI dependencies into local virtualenv
/home/sean/.hermes/hermes-webui/.venv/bin/python: No module named pip
[bootstrap] ERROR: Command '['/home/sean/.hermes/hermes-webui/.venv/bin/python', '-m', 'pip', 'install', '--quiet', '--upgrade', 'pip']' returned non-zero exit status 1.
```

**Root cause**: The `.venv` created by `python3 -m venv` was missing pip — either an incomplete venv creation or pip wasn't available in the Python environment.

**Fix**:
```bash
rm -rf ~/.hermes/hermes-webui/.venv
python3 -m venv ~/.hermes/hermes-webui/.venv
# pip is now available in the new venv
```

**Prevention**: If you see "No module named pip" on a fresh venv, recreate it rather than trying to install pip into it.

## Running hermes-webui

**Native Python (no Docker)**:
```bash
cd ~/.hermes/hermes-webui
./ctl.sh start  # uses bootstrap.py + ctl.sh PID management
./ctl.sh status
./ctl.sh stop
./ctl.sh logs
```

**Docker (recommended for persistence)**:
```bash
cd ~/.hermes/hermes-webui
docker compose up -d        # start
docker compose ps -a        # status
docker compose logs --tail 30  # logs
docker compose down         # stop
docker compose up --build -d  # rebuild + start
```

**Note on ctl.sh vs docker**: The `ctl.sh` script uses `bootstrap.py`. If the .venv is broken, it fails silently (process exits). Docker is more reliable because the container has its own isolated environment.

## Docker Compose Location

The hermes-webui has its **own** `docker-compose.yml` at:
```
~/.hermes/hermes-webui/docker-compose.yml
```

This is separate from the hermes-agent compose at:
```
~/.hermes/home/hermes-sync/docker/docker-compose.yml
```

Two different Docker projects — don't confuse them.

## Persistence: systemd User Service (Recommended)

hermes-webui runs inside Docker. The recommended persistent setup uses a **user-level** systemd service (no root/sudo needed).

### Prerequisites

```bash
# Enable linger (so user services start at boot without login)
loginctl enable-linger sean
```

### Service File

Create at `~/.config/systemd/user/hermes-webui.service`:

```ini
[Unit]
Description=Hermes Web UI (Docker)
After=network.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=%h/.hermes/hermes-webui
ExecStart=/usr/bin/docker compose -f %h/.hermes/hermes-webui/docker-compose.yml up -d
ExecStop=/usr/bin/docker compose -f %h/.hermes/hermes-webui/docker-compose.yml down
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

### Install & Enable

```bash
systemctl --user daemon-reload
systemctl --user enable --now hermes-webui.service

# Verify
systemctl --user status hermes-webui.service
docker ps --format '{{.Names}} {{.Status}}' | grep webui
curl -s -o /dev/null -w 'HTTP:%{http_code}' http://127.0.0.1:8787/
```

### Key Design Decisions

- **`Type=oneshot` + `RemainAfterExit=yes`**: `docker compose up -d` exits quickly (the container keeps running in the background). Without these, systemd thinks the service stopped and marks it inactive.
- **No `Requires=docker.service`**: User-level systemd cannot track the system Docker daemon as a dependency. The service assumes Docker is available.
- **`Restart=on-failure`**: Restarts if the container fails. The container's own `restart: unless-stopped` handles crash survival.
- **Linger enabled**: `loginctl enable-linger sean` ensures user services start at boot even if no one logs in.

### Why Not Native Python bootstrap?

`bootstrap.py` needs a Python with both WebUI deps (`yaml`) AND hermes-agent imports (`dotenv`). The agent lives inside the Docker container (`hermes`); the host Python has neither. The Docker compose approach runs the webui in its own container with a complete environment — no dependency conflicts.

### If the Service Won't Start

```bash
# Check logs
journalctl --user -u hermes-webui.service -n 50

# Manually verify Docker compose works
cd ~/.hermes/hermes-webui && docker compose up -d

# Then restart the service
systemctl --user restart hermes-webui.service
```

The container itself has `restart: unless-stopped` so it survives container restarts. The systemd unit ensures it starts at boot.

## bootstrap.py Health Check

hermes-webui has a `/health` endpoint. Once running:
```
curl http://127.0.0.1:8787/health
# → {"status": "ok", ...}
```

## Key Files

| File | Purpose |
|------|---------|
| `~/.hermes/hermes-webui/bootstrap.py` | App entry point — discovers agent, starts server |
| `~/.hermes/hermes-webui/server.py` | Actual web server (FastAPI-based) |
| `~/.hermes/hermes-webui/ctl.sh` | PID/log management for native python startup |
| `~/.hermes/hermes-webui/docker-compose.yml` | Container definition (restart: unless-stopped) |
| `~/.hermes/hermes-webui/.env.example` | Config template |
| `~/.hermes/hermes-webui/requirements.txt` | Only `pyyaml>=6.0` — heavy deps come from Hermes agent venv |

## Critical: HERMES_WEBUI_AGENT_DIR Environment Variable

**This is required for AIAgent imports to work.** Without it, `/api/skills`, chat streaming, and any feature needing the agent module fail with `ModuleNotFoundError: No module named 'agent'`.

The container mounts `~/.hermes` → `/home/hermeswebui/.hermes`. The hermes-agent source must be present at that path inside the container. If the source exists but the env var is not set, bootstrap.py discovers the path but the Python sys.path doesn't include it — so the import still fails.

```yaml
# In docker-compose.yml — add this to the environment block:
- HERMES_WEBUI_AGENT_DIR=/home/hermeswebui/.hermes/hermes-agent
```

**Why it's needed:** The webui container runs its Python with `/app/venv/bin/python`. This venv has the webui dependencies (PyYAML, aiohttp) but NOT the hermes-agent source. The agent source lives in `/home/hermeswebui/.hermes/hermes-agent/` (from the volume mount). `HERMES_WEBUI_AGENT_DIR` tells bootstrap.py where to find it, and bootstrap.py prepends that path to `PYTHONPATH` before starting the server.

**Without this env var:**
- `bootstrap.py` discovers the agent dir but doesn't add it to `sys.path` for `server.py`
- Server starts (port 8787 responds)
- `/api/skills` → `ModuleNotFoundError: No module named 'agent'`
- Chat streaming → `ImportError: AIAgent not available`
- `/health` → `ok` (misleading — the web server itself works, but agent integration fails)

**With this env var:** All agent features work. The skills list returns 152 skills, streaming works, etc.

**Clone the agent if missing (from host):**
```bash
# The hermes-agent source must exist at ~/.hermes/hermes-agent
cd ~/.hermes && git clone https://github.com/NousResearch/hermes-agent.git hermes-agent
```

**Minimal verify inside container:**
```bash
docker exec hermes-webui-hermes-webui-1 python -c "import sys; sys.path.insert(0, '/home/hermeswebui/.hermes/hermes-agent'); from agent.skill_utils import iter_skill_index_files; print('AIAgent OK')"
```

## Agent Discovery (bootstrap.py)

`bootstrap.py` auto-discovers the Hermes Agent by:
1. Checking `HERMES_WEBUI_AGENT_DIR` env var ← **ALWAYS SET THIS**
2. Looking for `~/.hermes/hermes-agent`
3. Walking up from the `hermes` CLI shebang (via `shutil.which("hermes")`)
4. Checking `REPO_ROOT.parent/hermes-agent`

The agent must have:
- `run_agent.py` at the root (contains `AIAgent` class)
- `agent/` subdirectory (for `from agent.skill_utils import ...`)

**Note:** Discovery via env var sets `HERMES_WEBUI_AGENT_DIR` in the environment, but bootstrap.py does NOT automatically prepend the agent dir to `sys.path` before launching server.py. The env var approach works only if the agent source is already installed in the webui venv via `pip install -e .` OR if the agent path is mounted at a location bootstrap.py already adds to `PYTHONPATH`. Setting the env var AND mounting the source is the working combination.

## Port Conflict Detection

If 8787 is already in use:
```bash
# Find what's on 8787
python3 -c "import socket; s=socket.socket(); r=s.connect_ex(('127.0.0.1', 8787)); print('OPEN' if r==0 else f'closed ({r})'); s.close()"
```

Common conflict: another hermes-webui process from a previous session.