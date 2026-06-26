---
name: container-app-serving
description: Serve web apps (Streamlit, Flask, etc.) from inside a Docker container so they are accessible from the host browser. Covers port binding, network debugging, background process management, and the Streamlit-specific deprecation of use_container_width.
when_to_use:
  - Starting a Streamlit/Flask/dev server inside the container
  - Forwarding container ports to the host browser
  - Debugging "connection refused" when you expect a port to be listening
  - Running a long-lived server process via Hermes terminal
triggers:
  - "serve this app"
  - "forward port"
  - "localhost refused to connect"
  - "start streamlit"
  - "run the app"
---

## HWC Server (hermes-web-computer)

The HWC server is a Go binary that serves both the Svelte frontend and the WebSocket API. It runs on the **host** at port **3005**.

### Check if running
```bash
ssh ... sean@172.19.0.1 "ss -tlnp | grep 3005"
```

### Start procedure (build in container → deploy to host)
See `go` skill → "HWC Build + Deploy Pattern" for the full pattern. Key points:
- Build in container with Go 1.26 toolchain
- Pipe binary to host via SSH (SCP times out)
- **Must start from `backend/` directory** so `../frontend/dist` resolves

### Port 3005 not reachable from container
The container cannot curl host:3005 directly. Verify via SSH:
```bash
ssh ... sean@172.19.0.1 "curl -s -o /dev/null -w '%{http_code}' http://localhost:3005/"
```

### Cloudflare tunnel
The existing cloudflared tunnels point to `http://backend:3001` (agent-os) and `http://172.19.0.2:8787` (Hermes gateway). There is **no tunnel for HWC on port 3005**. To expose HWC externally, either:
1. Create a new named tunnel for port 3005 using `cloudflared tunnel create hwc && cloudflared tunnel route dns hwc hwc.yourdomain.com`
2. Or add an ingress rule to an existing tunnel config pointing `hwc.yourdomain.com` → `http://localhost:3005`

### Audio bridge error (non-critical)
On startup, HWC logs: `audio bridge connect error: failed to WebSocket dial: Get "http://localhost:11235/api/chat": connection refused`. This is expected when Fun-Audio-Chat is not running. It does not affect core functionality.

### HWC WebSocket endpoint
```
ws://localhost:3005/ws
```
Test with: `websocat ws://localhost:3005/ws -c '{"protocol":"ui","method":"system.info","id":"1","ts":1}'`

### HWC API endpoints
| Endpoint | Description |
|----------|-------------|
| `GET /` | Serves frontend SPA |
| `GET /ws` | WebSocket (JSON-RPC) |
| `GET /api/system/metrics` | Host metrics (CPU/mem/net/temp) |
| `WS ui layout.update` | Tiling layout operations |
| `WS agent chat.send` | Stream chat to Hermes |

## Quick Start (Streamlit)

```bash
# From the project directory:
python3 -m streamlit run app.py \
  --server.port 8502 \
  --server.headless true \
  --server.address 0.0.0.0
```

Then start it as a Hermes background process:
```
terminal(command="cd /path && python3 -m streamlit run app.py --server.port 8502 --server.headless true --server.address 0.0.0.0", background=true)
```

## Networking

- **Container IP**: `172.19.0.2` (hermes container, when using bridge networking)
- **Host IP**: `172.19.0.1` (gateway from container, bridge mode)
- **Host LAN IP**: `192.168.1.x` (varies — check `hostname -I` on host)
- `--server.address 0.0.0.0` is required — without it the app only listens on 127.0.0.1 inside the container and is NOT reachable from the host
- **The hermes agent container uses `network_mode: host`** — it shares the host's network stack. `localhost` from inside the container IS the host. This means:
  - Ports bound in the container are directly on the host
  - `curl localhost:8787` from inside the container reaches the host's port 8787
  - SSHD on the host IS reachable via `localhost` from inside the container
  - The `172.19.0.x` bridge network may still exist for other containers (e.g., hermes-webui, gto-wizard) but the hermes agent container itself uses host networking

### Container-to-Host SSH Connectivity

**The SSH key at `/home/hermes/.ssh/id_ed25519` (referenced in the system prompt) is NOT accessible from inside the container.** The container's home is `/home/hermes/` but the key file may not be mounted or may have wrong permissions. Verify with `ls -la ~/.ssh/` from inside the container first.

When SSH from container to host fails:
- `Permission denied (publickey)` → key not found or not in authorized_keys
- `Connection refused` → SSHD not running (unlikely with host networking)
- `No such file or directory` → key path wrong (check `~/.ssh/` contents)

**Key paths (verify which exist):**
- `/home/hermes/.ssh/id_ed25519` — system prompt reference, may not be accessible
- `~/.ssh/id_ed25519` — container's own key (different from host key)

**If SSH is needed and the key is missing**, the container can still access the host via `localhost` (host networking) — SSH is only needed for operations that require host user context (e.g., `systemctl --user`). For those, run directly on the host terminal instead.

## Port Debugging

The container has no `ss`, `netstat`, or `lsof`. To check if a port is listening:

```bash
# Hex decode /proc/net/tcp — port is the hex value after the colon in local_address
cat /proc/net/tcp
# Port 8501 = 0x2136, 8502 = 0x2137
```

Or use Python:
```python
import socket
s = socket.socket()
try:
    s.connect(('127.0.0.1', 8502))
    print("Port 8502 is open")
except ConnectionRefusedError:
    print("Port 8502 is closed")
finally:
    s.close()
```

## Port Conflict Resolution — Escalation Path

When `kill`, `pkill -f`, and `fuser -k` all fail to release a port, the process may be stuck in a state where signals don't reach it (e.g., Hermes background process tracking, zombie state, or the process is in an uninterruptible sleep).

### Step 1: Find the exact PID holding the port

```python
import os, glob

for pid_dir in glob.glob('/proc/[0-9]*/'):
    pid = os.path.basename(pid_dir.rstrip('/'))
    try:
        fd_dir = os.path.join(pid_dir, 'fd')
        if not os.path.isdir(fd_dir):
            continue
        for fd in os.listdir(fd_dir):
            try:
                link = os.readlink(os.path.join(fd_dir, fd))
                if 'socket:' in link:
                    inode = link.split('[')[1].rstrip(']')
                    with open('/proc/net/tcp') as f:
                        for line in f:
                            if inode in line:
                                parts = line.split()
                                local = parts[1]
                                port = int(local.split(':')[1], 16)
                                with open(os.path.join(pid_dir, 'cmdline'), 'rb') as cf:
                                    cmd = cf.read().decode('utf-8', errors='ignore').replace('\x00', ' ')
                                print(f'PID {pid}: port {port}, cmd: {cmd[:80]}')
            except (OSError, IndexError, ValueError):
                continue
    except PermissionError:
        continue
```

### Step 2: Kill by PID (not by name)

```bash
# Kill the specific PID
kill -9 <PID>
sleep 3
# Verify port is free
python3 -c "import socket; s=socket.socket(); s.connect(('127.0.0.1', PORT))" 2>/dev/null && echo "Still open" || echo "Free"
```

### Step 3: If still stuck, check for Hermes background process tracking

Hermes `terminal(background=true)` processes are tracked by the Hermes framework. If the process was started via Hermes, it may respawn. Check:
```
process(action="list")
```
And kill via Hermes process management if needed.

### Step 4: Nuclear option — kill all Python processes on the port

```bash
# Find all PIDs with sockets on the target port and kill them all
for pid_dir in /proc/[0-9]*/; do
  pid=$(basename "$pid_dir")
  if [ -d "$pid_dir/fd" ]; then
    for fd in "$pid_dir/fd"/*; do
      link=$(readlink "$fd" 2>/dev/null)
      if echo "$link" 2>/dev/null | grep -q "socket"; then
        inode=$(echo "$link" | grep -o '\[[0-9]*\]' | tr -d '[]')
        if [ -n "$inode" ]; then
          for line in $(grep "$inode" /proc/net/tcp 2>/dev/null); do
            port=$(echo "$line" | awk '{print $2}' | cut -d: -f2)
            port_dec=$((16#$port))
            if [ "$port_dec" = "8501" ] || [ "$port_dec" = "8502" ]; then
              echo "Killing PID $pid (port $port_dec)"
              kill -9 "$pid" 2>/dev/null
            fi
          done
        fi
      fi
    done
  fi
done 2>/dev/null
```

## Hermes WebUI Service (hermes-webui.service)

The WebUI is a Python `server.py` managed by a systemd user unit at the host
(`~/.config/systemd/user/hermes-webui.service`). It runs directly (not Docker)
on port 8787.

### systemd exit-code 216/GROUP

**Symptom:** `systemctl --user start hermes-webui.service` fails immediately with
`code=exited, status=216/GROUP`. The service is `inactive (dead)`.

**Cause:** The systemd user session cannot set the process group when the service
is started from the Hermes container context. This is a known limitation — the
container's systemd user instance lacks proper slice delegation.

**Workaround — run as background process:**

```bash
# Start manually from the project directory
cd /home/sc/repos/hermes-webui
/home/sc/.hermes/hermes-agent/venv/bin/python server.py
```

In Hermes, use `terminal(background=true)` with `exec`:

```
terminal(
  command="cd /home/sc/repos/hermes-webui && exec /home/sc/.hermes/hermes-agent/venv/bin/python server.py",
  background=true
)
```

**CRITICAL: Use `exec` in the command.** Without it, the shell remains as the parent process and the Python process can get orphaned or killed when the shell exits. Also do NOT pipe output through `head`, `tail`, or similar — the pipe will cause the process to exit when the pipe buffer fills (e.g., `server.py 2>&1 | head -50` kills the server after 50 lines of output).

**Verify it's working:**
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8787/
# Expected: 200
```

**Note:** The systemd unit can be enabled (`systemctl --user enable`) for
automatic start at boot, but it will still fail with 216/GROUP until the
systemd user session issue is resolved. The background process approach is
the reliable fix.

### WebUI not reachable (502 Bad Gateway)

If the WebUI returns 502:
1. Check if the process is running: `ss -tlnp | grep 8787` or `curl localhost:8787`
2. If not running, start via the background process method above
3. Check the Hermes process log: `process(action="log", session_id="...")`
4. Common cause: the background process was killed (OOM, session end) and didn't auto-restart
5. **If ALL commands return exit code 130 (interrupted)**: The container is under resource pressure (CPU/OOM). Wait and retry, or restart the container. This manifests as every terminal command getting SIGTERM'd before completion.

## Background Process Rules

- **Use `terminal(background=true)`** — Hermes tracks the process lifecycle
- **Always use `exec`** in the command to replace the shell process: `exec python server.py` not `python server.py`
- **Do NOT pipe output** through `head`, `tail`, `grep`, etc. — pipes cause the process to exit when the reader closes
- **Do NOT use `nohup ... > file.log &`** — Hermes blocks shell-level background wrappers
- **Do NOT redirect stdout to a file before checking permissions** — `nohup cmd > log` fails with "Permission denied" if the log file exists with wrong ownership
- Log output goes to Hermes process log: `process(action="log", session_id="...")`
- **Background processes die when the Hermes session ends** — they do NOT persist across sessions. For persistent services, use systemd on the host.

## Next.js Dev Server Pitfalls

Next.js `next dev` processes can persist across Hermes sessions and silently serve stale code. This is the **zombie dev server** pattern:

### Detection
- You edit files, restart the server, but the browser still shows old content
- `curl` returns HTML with old class names or design tokens
- `npm run build` shows new code compiles fine, but `next dev` still serves old layout
- `EADDRINUSE: address already in use` when starting a new dev server

### Root Cause
Multiple `next-server` processes running on different ports accumulate across sessions. When a new process fails with EADDRINUSE, the old process keeps serving stale code. The shell-level `pkill` often fails because process names aren't `next` but `node`.

### Fix
```bash
# 1. Find all occupied ports
for port in 8555 8558 8559 8560 8562 8563 8564 8565; do
  lsof -i :$port 2>/dev/null | grep LISTEN && echo "port $port in use" || echo "port $port free"
done

# 2. Kill by port (not by process name — more reliable)
kill -9 $(lsof -t -i :PORT) 2>/dev/null

# 3. Verify all ports are free before starting
fuser -k PORT/tcp 2>/dev/null

# 4. Clear .next cache and start fresh
cd /workspace/project && rm -rf .next
export PATH="/home/hermeswebui/.hermes/home/.local/bin:$PATH"
npx next dev -p 8564 --hostname 0.0.0.0

# 5. Verify new layout is served
curl -sL http://localhost:8564/page | grep -c "new-design-token"
```

### Prevention
- Before each `npx next dev`, run `fuser -k PORT/tcp`
- Check with `lsof -i :PORT` before starting
- Use a different port temporarily for verification (`npx next dev -p 8565`)
- Verify the page content (grep for a token unique to the new code), not just HTTP status code

## Streamlit-Specific

- Streamlit binary path: `/home/hermeswebui/.hermes/home/.local/bin/streamlit` (not on default `PATH`)
- Use `python3 -m streamlit` instead of bare `streamlit`

## Venv Python Mismatch / Broken Symlinks

**Symptom:** `venv/bin/python` or `venv/bin/python3` is a symlink to a Python that doesn't exist on this container (e.g., `python3 -> /usr/bin/python3` or `python3.13 -> python3`). The venv was created on the host (different Python version) and the symlinks don't resolve in the container.

**Detection:**
```bash
/workspace/path/venv/bin/python --version 2>&1
# If "No such file or directory" — symlinks are broken
cat /workspace/path/venv/pyvenv.cfg
# Check `home` and `version` — if home=/usr/bin and container has no /usr/bin/python3, it's broken
```

**Fix:** Don't try to fix the venv. Use the system Python directly:
```bash
# Check what Python is available
python3 --version  # e.g., Python 3.12.13

# Install deps system-wide (pymssql is usually already present)
python3 -m pip install streamlit==1.58.0 plotly pandas altair pydeck

# Run with system Python
python3 -m streamlit run /workspace/path/app.py --server.port 8502 --server.headless true --server.address 0.0.0.0
```

**Why this works:** The container's system Python (3.12) has pymssql pre-installed. Adding streamlit/plotly/pandas via pip is fast. No need to recreate the venv.

## App Code Missing — Recovery Strategy

**Symptom:** `app.py` or other application source files are missing from the project directory. Only `venv/` exists.

**Recovery order:**
1. Check if the file exists elsewhere: `find /workspace -name "app.py" -not -path "*/venv/*" -not -path "*/__pycache__/*"`
2. Check git history: `git log --all --oneline -- "*app.py"` then `git show <commit>:path/to/app.py`
3. Check the host via SSH: `ssh ... sean@172.19.0.1 "find /home/sean -name 'app.py' -path '*streamlit*'"`
4. Check `/tmp/` for copies (e.g., `/tmp/auth_wrapper.py`)
5. If truly gone, rebuild from schema + enums + skill patterns (see `sql-server-docker` and this skill's references)

**Prevention:** Always commit app code to git. The venv should be in `.gitignore`, but `app.py`, `auth_wrapper.py`, configs, and SQL templates must be committed.

## Auth Wrapper — Cookie-Based Login (not 401 Basic Auth)

The deployed `auth_wrapper.py` for OneTag uses a **cookie-based login form**, NOT HTTP Basic Auth 401. Key differences:

- **First visit**: Returns HTTP 200 with an HTML login form (not 401 + `WWW-Authenticate`)
- **After login**: Sets an HMAC-signed session cookie, then proxies to Streamlit
- **All subsequent requests**: Check cookie validity before proxying
- **WebSocket support**: The proxy handles WebSocket upgrades for Streamlit's SSE

This avoids the Cloudflare challenge-on-401 issue where CF Access intercepts 401 responses.

**Do NOT confuse this with the HTTP Basic Auth proxy pattern** (which returns 401 and uses `Authorization` headers). The cookie-based pattern is the current deployed version as of 2026-06.

**GitHub source:** The canonical auth_wrapper.py lives in `ChonSong/forrest-plan-and-track` repo under `streamlit_onetag/auth_wrapper.py`. Always fetch from there rather than `/tmp/` copies which may be stale.

**Symptom:** `cloudflared tunnel run` or `cloudflared --config ... run` logs `ERR Register tunnel error from server side error="Unauthorized: Tunnel not found"`.

**Cause:** The tunnel ID in the credentials file doesn't match any active tunnel in the Cloudflare dashboard. Tunnels can be deleted, expired, or the credentials file can be stale.

**Fix:** Create a new tunnel:
```bash
cloudflared tunnel create <name>
# This creates a new credentials file
cloudflared tunnel route dns <name> <hostname>
# Update onetag-config.yml with new tunnel ID and credentials-file
```

**Note:** The old tunnel ID `b3200be4-a8a8-4381-980b-038e402d8702` for `onetag.codeovertcp.com` is invalid as of 2026-06-09.
- **Streamlit 1.58+**: `use_container_width=True` is deprecated **only in `st.plotly_chart()`** — use `width='stretch'` instead. It is still valid in `st.dataframe()` (different parameter, no deprecation). Apply globally with: `sed -i 's/use_container_width=True/width=stretch/g' app.py`

### Streamlit behind Cloudflare Tunnel

When serving Streamlit behind a Cloudflare tunnel, disable CORS and XSRF protection so the tunnel's forwarded requests aren't rejected. Use these flags:

```
--server.enableCORS false --server.enableXsrfProtection false
```

Without these, the main page may return HTTP 500 through the tunnel even though the health endpoint (`/_stcore/health`) works fine. The issue is that the tunnel's Host header differs from localhost, triggering Streamlit's CORS check.

#### Intermittent 500 with multiple HA connections

The Cloudflare tunnel creates multiple HA connections (default: 4) to different edge servers. Some connections may be stale, leading to **intermittent 500 responses** — alternating 200/500 on consecutive requests.

**Fix:** Reduce `--ha-connections` to 2:

```bash
cloudflared tunnel --protocol http2 --ha-connections 2 --config config.yml run
```

**Testing pattern** — all consecutive requests should return 200:
```bash
for i in 1 2 3 4 5; do
    curl -s -o /dev/null -w "%{http_code}" https://domain.com/ && echo ""
    sleep 1
done
```

Any 500 indicates a stale connection — restart with `--ha-connections 2`.

#### Local SQLite fallback for specific pages

When a Streamlit app depends on SQL Server that may be unavailable, individual pages can use a local SQLite database as fallback:

```python
def page_findings(flt):
    import os as _os
    _db_path = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), 'data', 'onetag.db')
    if not _os.path.exists(_db_path):
        st.error("Local database not found")
        return

    @st.cache_data(ttl=3600)
    def _run_forrest():
        import sys as _sys
        _repo_root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
        if _repo_root not in _sys.path:
            _sys.path.insert(0, _repo_root)  # needed for engine. imports
        import sqlite3 as _sqlite3
        _conn = _sqlite3.connect(_db_path)
        _conn.row_factory = _sqlite3.Row
        from engine.runner import run_all as _run_all
        _result = _run_all(_conn)
        _conn.close()
        return _result
```

Key: add `sys.path.insert(0, repo_root)` so Python imports resolve from the project root, not the Streamlit subdirectory.

### Graceful SQL Server disconnect

When a Streamlit app depends on SQL Server that may be unavailable, remove `st.stop()` on connection failure and instead show a warning. This lets other pages (like a local-SQLite findings page) still function:

```python
ok, ver = check_connection()
if ok:
    st.sidebar.success(f"Connected | {ver}")
else:
    st.sidebar.warning("SQL Server unavailable — some pages may not work")
    # Don't st.stop() — let other pages that use different data sources work
```

## Connection Management: Fresh Per-Query Pattern

**Problem:** `@st.cache_resource` caches a single connection that dies after SQL Server timeout. All subsequent queries get `DBPROCESS is dead or not enabled` or `Adaptive Server connection timed out`.

**Fix:** Open a fresh connection per query with retry logic. See `sql-server-docker` skill → `references/streamlit-sql-server-patterns.md` for the full pattern.

Key points:
- Never cache DB connections with `@st.cache_resource` — they go stale
- Use a `_new_connection()` helper with 3-attempt retry and 2-second backoff
- Catch `pymssql.OperationalError` specifically for retry; let other errors surface
- Always close connections in `finally` blocks

## Heavy Query Timeout Prevention

When a query joins many tables (5+) with many-to-many relationships:

1. **Reduce join count** — use `LEFT JOIN` instead of `INNER JOIN` for optional relations
2. **Remove non-essential CTEs** — pre-aggregation CTEs add overhead; only use when cartesian explosion is unavoidable
3. **Add `TOP N`** — always cap result sets on exploratory queries
4. **Simplify** — if a column isn't displayed, don't query it

See `sql-server-docker` skill → `references/sql-server-query-patterns.md` for the full SQL pattern reference.

## Soft-Delete Pattern

Every table has `DeletedDate`. Always filter it:
```sql
WHERE TableName.DeletedDate IS NULL
```

## Streamlit UI Patterns

See `sql-server-docker` skill → `references/streamlit-sql-server-patterns.md` for:
- Duration filter checkbox pattern (filter bad data with a toggle)
- SQL query display under tables (collapsible expander with `st.code`)
- Error boundary + reconnect button pattern
- Pandas `describe()` gotcha (no `sum` key — use `df[col].sum()`)
- Multi-pass cached function optimization (pass DataFrame instead of re-querying)

## SQL Server Schema Patterns (Reference)

When building queries against an unfamiliar SQL Server database:

1. **Check sys.columns first** — prevents "Invalid column name" errors
   ```sql
   SELECT name FROM sys.columns WHERE object_id = OBJECT_ID('TableName') ORDER BY column_id
   ```

2. **Pre-aggregate many-to-many in CTEs** — avoids cartesian explosion
   ```sql
   WITH IsoCounts AS (
       SELECT ri.RFIId, COUNT(DISTINCT ri.IsolationPointId) AS IsolationPointCount
       FROM RFIIsolations ri WHERE ri.DeletedDate IS NULL GROUP BY ri.RFIId
   )
   SELECT ... SUM(ic.IsolationPointCount) AS IsolationPointCount
   FROM ... LEFT JOIN IsoCounts ic ON r.Id = ic.RFIId ...
   ```

3. **Derive actual dates from activity tables** — Jobs have no ActualStartDate
   ```sql
   MIN(rlrj.LockOnDate) AS ActualStart, MAX(rlrj.LockOffDate) AS ActualEnd
   ```

4. **Always filter soft-deletes** — `WHERE TableName.DeletedDate IS NULL`

5. **Parameterized queries in Streamlit** — use `%(param)s` with dict params, pass through `cur.execute(sql, params)`

## SQL Server Query Patterns

See [`references/sql-server-patterns.md`](references/sql-server-patterns.md) for:
- `SELECT DISTINCT TOP N` syntax (DISTINCT must come before TOP)
- Dynamic WHERE clause builder pattern
- Pre-aggregation CTEs for many-to-many joins
- Column existence queries
- Date derivation from activity tables
- Null-safe Pandas comparisons
- Chart builder defensive patterns
- RFILogType enum reference
