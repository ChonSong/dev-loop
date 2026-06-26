# Docker DNS Resolution — glibc Parallel Query Hang

## Symptom

- `curl https://discord.com` works fine (HTTP 200)
- `curl wss://gateway.discord.gg` also works (curl uses c-ares resolver)
- **Python's `socket.getaddrinfo` hangs** for the same hostname (~30s+ timeout)
- Discord bot's WebSocket gateway connection times out even though REST API calls succeed
- Other CDN-backed hostnames (Cloudflare, Fastly) may also trigger this

## Root Cause

Docker containers use an internal DNS resolver at `127.0.0.11` that forwards to the host's DNS. glibc's `getaddrinfo()` sends **A (IPv4) and AAAA (IPv6) DNS queries in parallel**. Docker's resolver can get confused when both queries arrive simultaneously for CDN-backed hostnames that use DNS-based load balancing with multiple answer records, causing the query to hang or time out.

Curl's c-ares resolver doesn't have this issue — it handles parallel queries differently.

## How to Diagnose

```bash
# This works (curl uses c-ares)
curl -s https://discord.com/api/v10/gateway
# → {"url":"wss://gateway.discord.gg"}

# This works (curl resolves the CDN hostname)
curl -w "%{http_code}" -s -o /dev/null https://gateway.discord.gg
# → 200

# This TIMES OUT (glibc getaddrinfo hangs)
python3 -c "import socket; print(socket.getaddrinfo('gateway.discord.gg', 443))"
# → hangs indefinitely

# This VERIFIES the fix
RES_OPTIONS=single-request-reopen python3 -c \
  "import socket; print(socket.getaddrinfo('gateway.discord.gg', 443))"
# → resolves in ~5 seconds
```

## The Fix

Set the `RES_OPTIONS` environment variable to `single-request-reopen`:

```bash
# Shell
export RES_OPTIONS=single-request-reopen

# Per-command
RES_OPTIONS=single-request-reopen python3 your_script.py

# In docker-compose
environment:
  - RES_OPTIONS=single-request-reopen

# In Dockerfile
ENV RES_OPTIONS=single-request-reopen

# In ~/.hermes/.env
echo 'RES_OPTIONS=single-request-reopen' >> ~/.hermes/.env
```

### What `single-request-reopen` Does

Instructs glibc to issue A and AAAA queries **sequentially** instead of in parallel. The resolver reopens the UDP socket between queries, avoiding the race condition in Docker's forwarding resolver.

Alternative: `RES_OPTIONS=single-request` (keeps the same socket). `single-request-reopen` is generally more reliable for Docker environments.

### Alternative Fix: Install aiodns (c-ares)

For **aiohttp-based applications** (discord.py, some API clients), install `aiodns` so aiohttp uses the c-ares resolver instead of glibc's `getaddrinfo`:

```bash
pip install aiodns
```

After installation, aiohttp's `DefaultResolver` switches from `ThreadedResolver` (glibc) to `AsyncResolver` (c-ares). Verify:

```python
import aiohttp.resolver
print(aiohttp.resolver.DefaultResolver)
# → <class 'aiohttp.resolver.AsyncResolver'>   # c-ares in use
# → <class 'aiohttp.resolver.ThreadedResolver'> # glibc fallback
```

**When to use which fix:**

| Fix | Scope | Best for |
|-----|-------|----------|
| `RES_OPTIONS=single-request-reopen` | Global (process-wide) | Any Python app, includes subprocesses |
| `pip install aiodns` | Per-package (aiohttp only) | When you can't set env vars, or want a scoped fix |

Both can be applied together — `aiodns` provides the resolver, `RES_OPTIONS` is a safety net for anything using glibc directly.

## Affected Scenarios

- Discord bot WebSocket gateway connection (discord.py)
- Any Python library that uses `getaddrinfo` for DNS (aiohttp, httpx, requests)
- Services talking to CDN-backed APIs (Cloudflare, Fastly, Akamai)
- **Curl works fine** (uses c-ares) — don't rely on curl testing alone

## Prevention

Always add `RES_OPTIONS=single-request-reopen` to Docker container environments that run Python applications making external network calls, especially when:

- The app connects to WebSocket endpoints
- The app uses Discord, Slack, or other real-time API clients
- The app talks to CDN-backed APIs (Cloudflare, etc.)

## Debugging Deep Dive: Raw aiohttp Works But discord.py Doesn't

When DNS seems fixed (`aiodns` installed, `curl` works) but discord.py still times out on WebSocket, the issue may NOT be DNS at all.

### Key test

```python
import asyncio, aiohttp, time

async def test():
    async with aiohttp.ClientSession() as session:
        start = time.time()
        async with session.ws_connect(
            'wss://gateway.discord.gg/?v=10&encoding=json',
            timeout=15.0
        ) as ws:
            elapsed = time.time() - start
            print(f'WS connected in {elapsed:.2f}s')
            msg = await ws.receive(timeout=10)
            print(f'Hello: {msg.data[:200]}')

asyncio.run(test())
```

If this succeeds (should take ~0.3-2s) but discord.py's `client.start()` still fails, then:

1. **The network and DNS are fine** - the issue is in discord.py's client initialization
2. Check discord.py version: `pip show discord.py`
3. Check discord.py's internal HTTP session: created at `http.py:831` with `TCPConnector(limit=0)` — no custom resolver config
4. Compare the WebSocket URL: discord.py uses `http.ws_connect()` which passes proxy headers and `User-Agent` — a proxy configuration (via `DISCORD_PROXY` env or system proxy) could interfere with the WebSocket upgrade
5. Check for proxy env vars: `env | grep -i proxy`

### What discord.py actually does

```
client.start(token)
  → http.static_login(token)                    # REST: GET /users/@me (works)
    → creates aiohttp.ClientSession(connector=TCPConnector(limit=0))
  → client.connect()
    → http.ws_connect(url)                       # WebSocket: wss://gateway.discord.gg (may hang)
      → session.ws_connect(url, headers={...})   # passes proxy, User-Agent
```

The WebSocket connection goes through discord.py's `ws_connect` at `http.py:553` which adds `proxy`, `proxy_auth`, and `User-Agent` header. If discord.py's internal HTTP session was created **_before_** `aiodns` was installed, it won't use the c-ares resolver — aiohttp checks for aiodns at `TCPConnector` init time only.

**Diagnosis for proxy suspicion:**

```bash
# Check what proxy discord.py might pick up
echo "HTTPS_PROXY=$HTTPS_PROXY"
echo "HTTP_PROXY=$HTTP_PROXY"
echo "DISCORD_PROXY=$DISCORD_PROXY"
```

If any proxy is set, discord.py routes WebSocket through it, which can break the upgrade. Unset with:
```bash
unset HTTPS_PROXY HTTP_PROXY ALL_PROXY DISCORD_PROXY
```
