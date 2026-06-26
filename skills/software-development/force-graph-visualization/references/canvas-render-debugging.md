# Canvas Render Debugging for ForceGraph

Techniques for diagnosing when a ForceGraph canvas renders blank in headless Chrome despite valid JS and data.

## Confirmed VTB values (from production sessions)

| Graph size | VTB needed | Approach | Confirmed |
|-----------|-----------|----------|-----------|
| 821 nodes, 1298 edges inline (519KB HTML) | 15000ms | `--virtual-time-budget=15000` + `--screenshot` | ✅ Working (May 2026) |
| 1351 nodes, 2671 edges inline (990KB HTML) | 20000ms | `--virtual-time-budget=20000` + `--screenshot` | ✅ Working (May 2026) |
| 909 nodes, 1328 edges async fetch | 30000ms | `--virtual-time-budget=30000` + `--screenshot` | ✅ Working (May 2026) |

These serve as a starting point for similar-scale graphs. If edges don't render, increase VTB by 5000ms.

## PDF line-check technique (fallback when screenshots fail)

### Why it works

ForceGraph renders to a `<canvas>` element. When Chrome's headless PDF pipeline captures the page, canvas content is serialized as PDF path operators:

- `cm` (set matrix/concat) — coordinate transforms. These appear for ANY canvas element that Chrome processed, whether it has content or not.
- `l` (lineTo) — actual line segments. These only appear when pixels were actually drawn on the canvas.

An empty canvas produces `cm` ops but zero `l` ops. A rendered graph with edges produces many `l` ops.

### Procedure

```bash
# 1. Capture PDF
google-chrome-stable --headless --disable-gpu \
  --print-to-pdf=/tmp/graph.pdf --window-size=1600,900 \
  <url>

# 2. Check line operations
python3 -c "
with open('/tmp/graph.pdf','rb') as f:
    d = f.read()
line_ops = d.count(b' l ')
cm_ops = d.count(b' cm ')
print(f'Line ops (l): {line_ops}')
print(f'Matrix ops (cm): {cm_ops}')
if cm_ops > 0 and line_ops == 0:
    print('RESULT: Canvas exists but EMPTY — graph not rendering')
elif line_ops > 50:
    print('RESULT: Likely rendered — content visible')
else:
    print('RESULT: Ambiguous — check PDF manually')
"
```

## CDP runtime debugging (Python websocket-client)

When `--screenshot` is broken or `--print-to-pdf` shows empty canvas, use CDP with Python's `websocket-client` library to inspect the live runtime state.

### Why not Node.js?

The Node.js `ws` module is often not installed on the host. Python's `websocket-client` can be installed in a temporary venv:

```bash
python3 -m venv /tmp/shotenv
/tmp/shotenv/bin/pip install websocket-client
```

### Complete capture script

```python
import subprocess as sp, json, time, http.client, base64, sys, os
import websocket

PORT = 9227
ts = str(int(time.time()))
URL = f"https://example.github.io/repo/?t={ts}"

# Kill any existing Chrome on this port
sp.run(["pkill", "-f", f"remote-debugging-port={PORT}"], capture_output=True)
time.sleep(1)

# Launch Chrome with about:blank first (faster than navigating to target URL)
chrome = sp.Popen([
    "google-chrome-stable", "--headless", "--disable-gpu", "--no-sandbox",
    "--disable-software-rasterizer", "--disable-dev-shm-usage",
    f"--remote-debugging-port={PORT}",
    "--remote-allow-origins=*",  # ← REQUIRED for CDP websocket
    "about:blank"
], stdout=sp.DEVNULL, stderr=sp.DEVNULL)
time.sleep(3)

# Create a new tab with our URL via /json/new
conn = http.client.HTTPConnection("127.0.0.1", PORT)
conn.request("PUT", f"/json/new?{URL}")
conn.getresponse().read()
conn.close()
time.sleep(3)

# List pages and find our target tab
conn = http.client.HTTPConnection("127.0.0.1", PORT)
conn.request("GET", "/json")
pages = json.loads(conn.getresponse().read())
conn.close()

target_ws = None
for p in pages:
    u = p.get("url", "").lower()
    if "knowledge" in u or "skills" in u:
        target_ws = p["webSocketDebuggerUrl"]
        break
if not target_ws:
    target_ws = pages[0]["webSocketDebuggerUrl"]

# Connect and inspect runtime
ws = websocket.create_connection(target_ws, timeout=30,
    header=["Origin: http://127.0.0.1:9227"])

# Enable domains
ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
ws.recv()
ws.send(json.dumps({"id": 2, "method": "Page.enable"}))
ws.recv()

time.sleep(5)  # wait for page to render

# Check ForceGraph loaded
ws.send(json.dumps({"id": 11, "method": "Runtime.evaluate", "params": {
    "expression": "typeof ForceGraph === 'function'",
    "returnByValue": True
}}))
result = json.loads(ws.recv())
has_fg = result.get("result", {}).get("result", {}).get("value", False)
print(f"ForceGraph loaded: {has_fg}")

# Check D (graph data) loaded
ws.send(json.dumps({"id": 12, "method": "Runtime.evaluate", "params": {
    "expression": "typeof D !== 'undefined' && D !== null",
    "returnByValue": True
}}))
result = json.loads(ws.recv())
has_data = result.get("result", {}).get("result", {}).get("value", False)
print(f"D loaded: {has_data}")

# Take screenshot
time.sleep(8)
ws.send(json.dumps({"id": 20, "method": "Page.captureScreenshot", "params": {"format": "png"}}))
result = json.loads(ws.recv())
ws.close()

if "result" in result and "data" in result["result"]:
    img = base64.b64decode(result["result"]["data"])
    with open("/tmp/screenshot.png", "wb") as f:
        f.write(img)
    print(f"Screenshot: {len(img)} bytes")

chrome.terminate()
chrome.wait()
```

### CDP response interpretation

| CDP response | Meaning |
|---|---|
| `ForceGraph: false` | CDN script failed to load in headless mode (jsdelivr timeout, CSP issue, or network offline) |
| `D loaded: false` | Data script failed (file not found, JS parse error, or the page Chrome rendered differs from curl output — GitHub Pages cache) |
| Both true, screenshot small (25-46KB) | ForceGraph initialized but tag edge computation or CDN init blocks rendering. Check if `warmupTicks` is too high or `computeTagEdges` is running synchronously on a large tag group |
| `403 Forbidden` on WebSocket connect | Missing `--remote-allow-origins=*` flag on Chrome startup |

### key flags for CDP

```bash
--remote-debugging-port=9227   # Required: enables CDP endpoint
--remote-allow-origins=*       # Required: allows websocket connections from any origin
--headless                     # Required: run without window
about:blank                    # Start blank, navigate after CDP attaches (avoids page-render-before-CDP-attached race)
```

Starting with `about:blank` is critical — if Chrome starts directly at the target URL, the page may fully load and paint before CDP attaches, and you miss the initial render.

## `--virtual-time-budget` kills `onEngineStop` (critical timing bug)

When using headless Chrome with `--virtual-time-budget` to screenshot a force-graph page that loads data via `fetch()`, the VTB timer starts from page navigation — NOT from JS idle. For a 1351-node graph with hub-and-spoke edges:

```
Timeline:
  T=0s    Page load starts, VTB timer begins
  T=0.5s  CDN scripts downloaded
  T=1s    fetch('graph_data.json') starts
  T=1.5s  600KB JSON parsed
  T=3s    ForceGraph() created, warmupTicks run
  T=8s    Simulation still settling (cooldownTicks not reached)
  T=10s   VTB EXCEEDED — Chrome FREEZES all JS execution
          onEngineStop NEVER FIRES → graph captures with 0 edges rendered
  T=10s+  Screenshot shows nodes (placed by warmupTicks) but NO edges
```

**Root cause**: ForceGraph's `onEngineStop` fires only after the simulation reaches equilibrium (no changes for `cooldownTicks` consecutive ticks). With 1000+ nodes and hub-and-spoke topology, the simulation takes 8-15s to settle. VTB kills it midway.

**Solutions (in order of reliability):**

| Solution | VTB needed | Edge rendering | Notes |
|----------|-----------|----------------|-------|
| **PDF line-check** | N/A — capture after page is done | Confirmed by `l` ops in PDF byte analysis | Most reliable; doesn't depend on VTB timing |
| **Inline data + high VTB** | 20000-30000ms | Good | No fetch latency; HTML larger but simulation starts immediately |
| **Async fetch + high VTB** | 20000-30000ms | Marginal | VTB must cover fetch + parse + full simulation settle |
| **CDP `Runtime.evaluate`** | N/A — interact with live JS | Confirmed by checking `document.querySelector('canvas').toDataURL()` in real-time | Requires Python websocket-client; no VTB at all |

**Workaround for async fetch**: Set `--virtual-time-budget=30000` and test locally first to confirm onEngineStop fires before VTB expires. Monitor by adding a timestamp log:

```javascript
const t0 = performance.now();
graph.onEngineStop(() => {
  console.log(`Settled at ${(performance.now()-t0).toFixed(0)}ms`);
  graph.zoomToFit(400, 120);
});
```

If the settle time exceeds your VTB setting, reduce `warmupTicks`, `cooldownTicks`, or increase `d3AlphaDecay` to make the simulation converge faster. For 1351-node hub-and-spoke graphs, these values converge in ~10s:

```javascript
.d3AlphaDecay(0.02)
.d3VelocityDecay(0.3)
.warmupTicks(100)
.cooldownTicks(30)
```

## GitHub Pages deployment debugging

### Stale content diagnosis

```bash
# Check what the live page actually contains
curl -sL https://chonsong.github.io/<repo>/ | grep -c '<your-change-signature>'

# Check with cache-busting
curl -sL 'https://chonsong.github.io/<repo>/?v=$(date +%s)' | grep -c '<signature>'

# Headers show when page was last modified
curl -sI https://chonsong.github.io/<repo>/ | grep -i last-modified
```

### Verifying git push worked

```bash
git log --oneline -3       # Confirm your commit is at HEAD
git push origin main       # Confirm push succeeded
# Wait 15-30 seconds
curl -sL <url> | head -5   # Check live content updated
```

### Common GitHub Pages cache causes for blank canvas

1. **DNS/propagation delay** — new deployments may not be live for 1-2 minutes
2. **CloudFlare or Fastly edge cache** — even after Pages updates, CDN edge may serve stale version
3. **Browser cache** — headless Chrome may use local cache; use `--incognito` or `?v=` param
4. **Pages build failure** — GitHub Actions build log shows errors; check the Deployments tab
5. **404 for data files** — if using async fetch, the `.json` file may 404 or still be the old version
