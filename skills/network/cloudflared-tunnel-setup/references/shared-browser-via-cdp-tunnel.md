# Shared Browser via CDP + Cloudflare Tunnel

A co-browsing setup where the AI and human share the same live browser session. The AI controls Chrome via CDP (Chrome DevTools Protocol), and the human watches (and can interact) through a web-based viewer proxied through Cloudflare Tunnel.

## Architecture

```
AI (Hermes) --curl--> Shared Browser Viewer (:3099) --CDP--> Chrome (:9222)
                                                                |
Human (browser) --https://browse.codeovertcp.com--> Cloudflare Tunnel --> :3099
```

## Components

### 1. Chrome with Remote Debugging

Launch Chromium (from Playwright's cache) with `--remote-debugging-port` on a virtual display:

```bash
# Install Playwright's Chromium
npx playwright install chromium

# Find Chromium binary
ls ~/.cache/ms-playwright/chromium-*/chrome-linux64/chrome

# Start Xvfb virtual display
Xvfb :99 -screen 0 1920x1080x24 +extension GLX +render -noreset &

# Launch Chromium headed
DISPLAY=:99 /path/to/chrome \
  --no-sandbox \
  --disable-gpu \
  --disable-dev-shm-usage \
  --remote-debugging-port=9222 \
  --remote-allow-origins=* \
  --window-size=1920,1080 \
  --user-data-dir=/tmp/chrome-tandem \
  --no-first-run
```

Chrome reports the CDP websocket URL at `http://127.0.0.1:9222/json/version`.
List open pages at `http://127.0.0.1:9222/json`.
Each page has a `webSocketDebuggerUrl` for CDP control.

### 2. Shared Browser Viewer (Node.js)

A lightweight HTTP server that:
- Captures screenshots via CDP (`Page.captureScreenshot`) — served at `/screenshot.png`
- Navigates on POST `/navigate` (via `Page.navigate`)
- Handles clicks on POST `/click` (via `Input.dispatchMouseEvent`)
- Handles text input on POST `/type` (via `Input.insertText`)
- Serves an HTML viewer with an auto-refreshing screenshot image

Key CDP domains to enable: `Page.enable`, `DOM.enable`.

The viewer runs on port 3099 and requires the `ws` npm package for CDP WebSocket connections.

### 3. Cloudflare Tunnel Exposure

```yaml
# /home/sc/.cloudflared/config.yml ingress addition
- hostname: browse.codeovertcp.com
  service: http://localhost:3099
```

**CRITICAL: DNS CNAME must use tunnel UUID** — `ddaeb2d9-...-uuid...cfargotunnel.com`, NOT the tunnel name. Compare against working records:

```bash
# Good (existing working):
hex.codeovertcp.com  CNAME -> ddaeb2d9-{uuid}.cfargotunnel.com

# Bad:
browse.codeovertcp.com  CNAME -> codeovertcp.cfargotunnel.com  # RETURNS 530
```

### 4. Restarting the Tunnel for New Ingress

Adding a new hostname to `config.yml` requires a full tunnel restart, not just SIGHUP:

```bash
# Kill ALL cloudflared PIDs (including wrapper scripts)
ps aux | grep cloudflared | grep -v grep | awk '{print $2}' | xargs kill -9

# Wait, verify no PIDs remain
sleep 2
ps aux | grep cloudflared | grep -v grep

# Restart fresh
cloudflared tunnel --config /home/sc/.cloudflared/config.yml run codeovertcp
```

## Browser Control from Hermes

With the viewer running, the AI can control the browser via curl:

```bash
# Navigate
curl -s -X POST http://127.0.0.1:3099/navigate \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}'

# Get screenshot
curl -s http://127.0.0.1:3099/screenshot.png -o /tmp/ss.png

# Get page info
curl -s http://127.0.0.1:3099/info
```

## Pitfalls

- **Xvfb is required** — Chromium won't launch in headed mode without a display
- **Playwright Chromium** requires glibc 2.25+ but works on Ubuntu 20.04 (glibc 2.31)
- **Electron apps (Tandem Browser)** may require newer glibc (2.33+) — incompatible with Ubuntu 20.04
- **POST through Cloudflare Tunnel** may return 530 for API endpoints; use localhost for control, tunnel for read-only viewing
- **Screenshot auto-refresh** at 2s intervals is visible in the viewer HTML; the img tag's `src` gets a timestamp query param to bypass cache
