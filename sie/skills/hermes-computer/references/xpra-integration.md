# Xpra Integration — hermes-web-computer

## What It Is

Xpra provides a **native Linux GUI escape hatch** for hermes-web-computer. When the user clicks "Xpra" in the dock, the backend starts an Xpra server in HTML5 mode and the frontend renders it in an iframe tile.

## Architecture

```
Browser → /api/xpra/* → Go ProxyHandler → Xpra HTML5 (localhost:9453+DISPLAY)
```

The frontend iframe points to `/api/xpra/` which is reverse-proxied to the Xpra HTML5 server. This avoids CORS issues (browser stays on same origin).

## Files

| File | Role |
|------|------|
| `backend/xpra/manager.go` | Server lifecycle: `Manager{Start,Stop,AttachWindow,IsRunning,HTTPURL,Display}` |
| `backend/xpra/proxy.go` | `ProxyHandler` (HTTP reverse proxy) + `WaitForServer` (polling) |
| `backend/ws/multiplexer.go` | Added `xpraMgr *xpra.Manager` field, `SetXpraManager()`, `InitializeXpra()`, `handleXpraProxy()` route |
| `backend/ws/apps.go` | Added `xpra` app type in `handleAppsList` + `case "xpra"` in `handleAppsLaunch` (lazy-start) |
| `backend/cmd/server/main.go` | Calls `mux.InitializeXpra(10)` at startup |
| `frontend/src/components/XpraTile.svelte` | Iframe tile: loading spinner, error state, retry button |
| `frontend/src/components/Tile.svelte` | Routes `node.content === 'xpra'` to `XpraTile` |
| `frontend/src/stores/ws.ts` | Added `http_url?: string`, `display?: string` to `LayoutTree` |

## Key Design Decisions

### Display `:10`
Fixed startup display. Xpra maps display number to port: `port = 9453 + display`. Display `:10` → port `9463`. Avoids collision with commonly-used ports.

### Lazy-Start Pattern
`Manager` is created at backend startup, but `Start()` is called on first `apps.launch` call. This avoids blocking on a server that may never be used.

### Graceful Degradation
`checkXpra()` uses `exec.LookPath("xpra")`. If absent, `InitializeXpra` logs `"xpra initialization failed"` and continues. The UI shows an error via `apps.error` event.

### No Xvfb Args
Xpra starts its own Xvfb internally. Do NOT pass explicit Xvfb arguments to `Start()` — that causes double-Xvfb issues.

### `http_url` / `display` Flow
1. `apps.launch{type:"xpra"}` → backend calls `xpraMgr.Start()` → returns `http_url` + `display`
2. Backend sends `apps.launch.response{http_url, display}` event
3. Frontend stores `http_url` + `display` on the `LayoutTree` node
4. `XpraTile.svelte` receives as props, builds iframe URL from `httpUrl` + `display`

### `$derived()` for srcUrl
Use `$derived()` so the iframe URL stays reactive if `httpUrl` or `display` props change:
```svelte
let srcUrl = $derived(`${$props.httpUrl}/index.html`)
```

## Go Build Verification

After patching `multiplexer.go` or `apps.go` in multi-agent sessions, check for import block corruption:
```bash
cd /opt/data/hermes-web-computer/backend
GOPATH=/opt/data/home/go go build -o /opt/data/hwc-server ./cmd/server/
```
Import corruption from duplicate patches manifests as "undefined: Multiplexer" or "undefined: xpra" even when the packages are correct. Fix by writing the import block cleanly.

## Discord Notification (HTTP 403)

Discord REST API v10 returns `403 Forbidden` when the bot token is invalid/expired or lacks channel permissions. Cloudflare proxy can also return a 1010 block page. Non-critical — phase completes regardless.

**Diagnosis:**
```python
import urllib.request
with open('/opt/data/.env') as f: content = f.read()
token = content.split('DISCORD_BOT_TOKEN=')[1].split('\n')[0]
req = urllib.request.Request(f'https://discord.com/api/v10/channels/{channel}',
    headers={'Authorization': f'Bot {token}'}, method='GET')
try: resp = urllib.request.urlopen(req, timeout=10)
except urllib.error.HTTPError as e: print(f"HTTP {e.code}")
```

**Fix:** Regenerate token at https://discord.com/developers/applications

## SSH Tunnel for XPra (Not Started)

The feature tracker marks SSH tunnel support as `⚪ not-started`. This enables browsers on remote machines to reach the host Xpra server via an SSH port forward. Pattern: `ssh -L 9453:localhost:9453 user@host` to forward the Xpra port.