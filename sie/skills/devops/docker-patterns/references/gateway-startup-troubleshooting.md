# Gateway Startup Troubleshooting in Docker

The Hermes Gateway (`hermes gateway run`) starts platform adapters (Discord, Matrix, Telegram) and the cron scheduler. It runs as a background process in the Hermes WebUI container.

## Symptoms of Startup Failure

| Symptom | Likely Cause |
|---------|-------------|
| Gateway process runs but **no state file** written (`gateway_state.json` missing for 60s+) | MCP server blocking startup (unreachable host) |
| State shows `"state": "retrying"` with `"discord connect timed out"` | DNS / WebSocket issue (see `docker-dns-resolution.md`) |
| Gateway process becomes **zombie** (state `Z` in /proc) | Started from execute_code sandbox (seccomp kills child) |
| Gateway prints startup banner then **silent for minutes** | Blocked on MCP discovery (see below) |

## Diagnosis Commands

```bash
# Check gateway state
cat ~/.hermes/gateway_state.json

# Check gateway logs
tail -50 ~/.hermes/logs/gateway.log

# Check if Discord registered commands
grep -i "registered\|discord\|error" ~/.hermes/logs/gateway.log

# Check if process is alive
kill -0 <PID> 2>/dev/null && echo ALIVE || echo DEAD

# Check process state (Z = zombie)
cat /proc/<PID>/status | grep State
```

## MCP Server Blocks Startup

**Root cause:** The gateway runs `discover_mcp_tools()` at line 15834 of `run.py` during startup. If any configured MCP server points to an unreachable host (e.g., a LAN IP like `192.168.1.102` not reachable from the container), the discovery blocks the entire startup sequence.

**Symptoms:**

- Gateway starts, prints deprecation warnings and skill collision warnings, then goes **silent for 30s+**
- No `gateway_state.json` written
- No health endpoint at `localhost:8642/health`
- Process is alive but not progressing

**Fix:**

1. Temporarily disable unreachable MCP servers in `~/.hermes/config.yaml`:
   ```yaml
   mcp_servers: {}     # Disable all, or remove the specific server
   ```

2. Clean stale state:
   ```bash
   rm -f ~/.hermes/gateway.lock ~/.hermes/gateway.pid ~/.hermes/gateway_state.json
   ```

3. Restart the gateway.

4. If the MCP server is needed, either make it reachable from the container or run it on the container host and use the host's IP (`172.17.0.1` from Docker bridge).

## Cleanup Sequence for Stale Gateway

When the gateway dies uncleanly (killed, container restart, zombie), leftover files prevent a fresh start:

```bash
rm -f ~/.hermes/gateway.lock ~/.hermes/gateway.pid ~/.hermes/gateway_state.json
```

Also check for lingering processes:
```bash
# Alpine/busybox
kill $(cat ~/.hermes/gateway.pid 2>/dev/null) 2>/dev/null
# Or find by name
for p in $(grep -l hermes /proc/*/cmdline 2>/dev/null); do
    pid=$(echo $p | cut -d/ -f3)
    [ "$pid" != "1" ] && kill $pid 2>/dev/null
done
```

## How to Start the Gateway

**From terminal(background=true) — CORRECT:**
```bash
HOME=/home/hermeswebui/.hermes/home /app/venv/bin/hermes gateway run
```
The process stays alive across tool calls and writes state.

**From execute_code — WRONG:**
```python
subprocess.Popen(["/app/venv/bin/hermes", "gateway", "run"])
```
The execute_code sandbox has restrictive seccomp filters. Child processes become zombies when the sandbox script exits because PID 1 (the container entrypoint) doesn't reap them.

**From terminal(background=true) with env overrides:**
```bash
RES_OPTIONS=single-request-reopen HOME=/home/hermeswebui/.hermes/home /app/venv/bin/hermes gateway run
```

## Gateway State File Format

```json
{
  "pid": 21373,
  "gateway_state": "running",
  "exit_reason": null,
  "platforms": {
    "discord": {
      "state": "connecting | connected | retrying | disconnected",
      "error_message": "discord connect timed out after 30s"
    },
    "matrix": {
      "state": "connecting | connected | retrying | disconnected",
      "error_message": "failed to connect"
    }
  }
}
```

States:
- `starting` — Gateway initializing, no platforms attempted yet
- `running` — Gateway is up (may have partial/failed platform connections)
- `startup_failed` — All platforms failed, gateway will retry
- `retrying` — Platform adapter is in reconnect loop

## Common Pitfalls

| Mistake | Consequence | Fix |
|---------|-------------|-----|
| Starting gateway from execute_code() | Zombie process, no state file | Use terminal(background=true) |
| Killing PID 7 (init script's child) | Breaks containers terminal execution | Kill children, not PID 1 |
| Not setting HOME correctly | Gateway reads wrong config/.env | Set `HOME=/home/hermeswebui/.hermes/home` |
| Forgetting to clean lock/pid files | "Already running" error on restart | `rm -f gateway.lock gateway.pid` |
| Removing gateway_state.json without killing process | Process writes old state, confusing diagnostics | Kill first, then clean |

## Config Duality: Two .hermes Locations

In the Hermes WebUI container, `HOME` is overridden to `/home/hermeswebui/.hermes/home` by the init script. This creates **two separate `.hermes` directories**:

| Path | Purpose | Contains |
|------|---------|----------|
| `/home/hermeswebui/.hermes/` | Outer - user's actual home | Env vars set by Docker compose (`DISCORD_BOT_TOKEN`, API keys) |
| `/home/hermeswebui/.hermes/home/.hermes/` | Inner - gateway's effective `~/.hermes/` (because `HOME=~/.hermes/home`) | Full config.yaml, skills, cron, gateway state |

**How the gateway resolves its config:**

- Config: reads `$HOME/.hermes/config.yaml` -> inner path
- `.env`: reads `$HOME/.hermes/.env` -> inner path
- ENV_IGNORELIST (from init script): `HOME PWD USER ...` - prevents HOME from being overwritten by .env

**Common failure: token in wrong .env**

The Discord bot token is often set via Docker environment or the outer `.env`, but the gateway reads from the inner `.env`. The fix:

```bash
echo 'DISCORD_BOT_TOKEN=***' >> /home/hermeswebui/.hermes/home/.hermes/.env
echo 'DISCORD_ALLOWED_USERS=your_id' >> /home/hermeswebui/.hermes/home/.hermes/.env
```

**Diagnosis:**

```bash
# Check which .env the gateway is actually reading
cat /proc/<gateway-pid>/environ 2>/dev/null | tr '\0' '\n' | grep DISCORD
# Or compare:
grep DISCORD /home/hermeswebui/.hermes/.env          # outer
grep DISCORD /home/hermeswebui/.hermes/home/.hermes/.env  # inner
```
