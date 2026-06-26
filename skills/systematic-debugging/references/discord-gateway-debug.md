# Discord Gateway Connectivity — Debug Reference

## Dual Config Problem (June 2026)

**The gateway reads from `$HERMES_HOME/config.yaml`, NOT `$HOME/.hermes/config.yaml`.**

Hermes Agent has two config directories:
- **Outer** (`$HERMES_HOME`): `/home/hermeswebui/.hermes/` — used by the gateway runtime
- **Inner** (`$HOME/.hermes/`): `/home/hermeswebui/.hermes/home/.hermes/` — NOT used by the gateway

`get_hermes_home()` returns `$HERMES_HOME` when set. The `.env` file, `config.yaml`, logs, PID file, and state all live under `$HERMES_HOME`.

**Danger:** If you fix `~/.hermes/home/.hermes/config.yaml` (the inner one), the gateway ignores it entirely. All config fixes must go to `$HERMES_HOME/config.yaml`.

**Check which config the gateway uses:**
```python
from hermes_cli.config import get_hermes_home
print(get_hermes_home())  # → /home/hermeswebui/.hermes
```

## MCP Server Blocking Gateway Startup

An unreachable MCP server blocks gateway startup. The gateway calls `discover_mcp_tools()` via `_loop.run_in_executor()` in `start_gateway()` (run.py:15837) **before** connecting any platform adapters.

If a configured MCP server points to a LAN address (e.g., `192.168.1.102:443` for TrueNAS) that isn't reachable from the container, `discover_mcp_tools()` hangs for the `connect_timeout` duration (default 30s, config timeout 120s).

**Symptoms:**
- Gateway process stays alive but produces no logs after the "WARNING hermes_cli.commands: Discord /skill:" collision messages
- State file is never written (`gateway_state.json` doesn't appear)
- No "Connecting to discord..." log message appears
- Killing and restarting shows the same pattern

**Fix:** Remove or comment out unreachable MCP servers from `$HERMES_HOME/config.yaml`:
```yaml
mcp_servers: {}  # or omit the section entirely
```

## Discord Connection Debugging Checklist

When Discord is "retrying" with "discord connect timed out after Ns":

### 1. Check Token Presence
```bash
grep DISCORD_BOT_TOKEN $HERMES_HOME/.env
```
The token MUST be in the `$HERMES_HOME/.env` file (not the inner one).

### 2. Check Config Permissions
```yaml
# $HERMES_HOME/config.yaml must have:
discord:
  require_mention: false      # true = must @mention the bot
  allowed_channels: "<ids>"   # empty = no channels allowed
```

### 3. Test Raw WebSocket Connectivity
Isolate whether discord.py has a client startup issue vs. a network issue:
```python
import asyncio, aiohttp, time, yarl, json
from discord.http import DiscordClientWebSocketResponse, INTERNAL_API_VERSION

async def test():
    connector = aiohttp.TCPConnector(limit=0)
    async with aiohttp.ClientSession(
        connector=connector,
        ws_response_class=DiscordClientWebSocketResponse,
        cookie_jar=aiohttp.DummyCookieJar(),
    ) as session:
        url = str(yarl.URL('wss://gateway.discord.gg/').with_query(v=INTERNAL_API_VERSION, encoding='json'))
        kwargs = {
            'proxy_auth': None, 'proxy': None, 'max_msg_size': 0,
            'timeout': aiohttp.ClientWSTimeout(ws_close=30.0),
            'autoclose': False,
            'headers': {'User-Agent': 'DiscordBot (https://github.com/Rapptz/discord.py 2.7.1) Python/3.12 aiohttp/3.13.4'},
        }
        start = time.time()
        async with session.ws_connect(url, **kwargs) as ws:
            elapsed = time.time() - start
            msg = await ws.receive(timeout=10)
            data = json.loads(msg.data)
            print(f'Connected in {elapsed:.2f}s - op={data["op"]}')

asyncio.run(test())
```
If raw WS connects (<1s) but discord.py client doesn't, the issue is in discord.py's client startup flow, not network.

### 4. Check for Docker DNS Glibc Issue
Docker's internal DNS resolver (127.0.0.11) chokes on glibc's parallel A/AAA queries for CDN-backed hostnames like `gateway.discord.gg`.

**Diagnose:** Python hangs on `socket.getaddrinfo('gateway.discord.gg', 443)`

**Fixes (in order of reliability):**
1. Install `aiodns` — makes aiohttp use c-ares resolver (like curl) instead of glibc:
   ```bash
   pip install aiodns  # or pip install "discord.py[speed]"
   ```
2. Set `RES_OPTIONS=single-request-reopen` in `.env` — makes glibc send A/AAAA sequentially

### 5. Connection Timeout Tuning

The 30s default timeout for discord.py's WebSocket handshake may be too tight in container environments. The adapter at `plugins/platforms/discord/adapter.py:904` has an inner timeout:
```python
await asyncio.wait_for(self._ready_event.wait(), timeout=60)
```
And the gateway runner at `run.py:2426` wraps `adapter.connect()` in another:
```python
return await asyncio.wait_for(adapter.connect(), timeout=timeout)
```
Keep both in sync (60s each) so the inner timeout fires first with a more specific error.

## Gateway Log Locations

All relative to `$HERMES_HOME/logs/`:
- `gateway.log` — main gateway events
- `agent.log` — per-session agent activity
- `gateway-exit-diag.log` — shutdown diagnostics
- `tui_gateway_crash.log` — TUI crash handler

## Architecture: From Config to Launch

```
$HERMES_HOME/config.yaml
    → GatewayRunner.start() iterates self.config.platforms
    → _create_adapter(Platform.DISCORD, platform_config)
    → DiscordAdapter.connect():
        1. Load opus codec
        2. Parse allowed users/roles from env
        3. Set intents (message_content, guild_messages, dm_messages, members, voice_states)
        4. Check DISCORD_PROXY env var
        5. Create commands.Bot(command_prefix="!", intents=intents)
        6. Register event handlers (on_ready, on_message, etc.)
        7. Register slash commands (/skill, /new, /reset, etc.)
        8. asyncio.create_task(client.start(token))  → login + WebSocket
        9. asyncio.wait_for(ready_event.wait(), timeout=60)
    → on_ready fires → ready_event.set() → connect() returns True
```

**discord.py startup inside client.start():**
1. `login(token)` → HTTP POST `/users/@me` (REST API — succeeds even when WS fails)
2. `connect()` → `DiscordWebSocket.from_client()` → WebSocket to `wss://gateway.discord.gg/`
3. Hello (op 10) → Identify (op 2) → Ready (op 0) → `on_ready` fires

**The REST API succeeding does NOT mean WebSocket works** — they use different connections and different hostnames (`discord.com` vs `gateway.discord.gg`).
