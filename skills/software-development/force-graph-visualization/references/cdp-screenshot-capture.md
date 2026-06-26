# CDP Screenshot Capture for ForceGraph Pages

Headless Chrome's `--screenshot` flag often captures blank canvases from force-graph pages because the simulation hasn't settled, or the flag itself is broken (Chrome 143+). Use Chrome DevTools Protocol (CDP) via Python + websocket-client for reliable canvas screenshots.

## Prerequisites on host

```bash
python3 -m venv /tmp/shotenv
/tmp/shotenv/bin/pip install websocket-client
```

## Full capture script

```python
#!/usr/bin/env python3
import json, http.client, time, base64, subprocess, websocket

PORT = 9227
ts = str(int(time.time()))
URL = "https://example.com/graph/?t=" + ts

# Kill stale
subprocess.run(["pkill", "-f", f"remote-debugging-port={PORT}"], capture_output=True)
time.sleep(1)

# Launch Chrome on about:blank
chrome = subprocess.Popen([
    "google-chrome-stable", "--headless", "--disable-gpu", "--no-sandbox",
    "--remote-debugging-port=" + str(PORT), "--remote-allow-origins=*",
    "about:blank"
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(3)

# Create page tab
conn = http.client.HTTPConnection("127.0.0.1", PORT)
conn.request("PUT", "/json/new?" + URL)
conn.getresponse().read()
conn.close()
time.sleep(3)

# Find our page
conn = http.client.HTTPConnection("127.0.0.1", PORT)
conn.request("GET", "/json")
pages = json.loads(conn.getresponse().read())
conn.close()

target = pages[0]
for p in pages:
    if "knowledge" in p.get("url", "").lower():
        target = p
        break

ws_url = target["webSocketDebuggerUrl"]
ws = websocket.create_connection(ws_url, timeout=30,
    header=["Origin: http://127.0.0.1:" + str(PORT)])

def cdp(method, params=None):
    msg = {"id": int(time.time() * 1000), "method": method}
    if params: msg["params"] = params
    ws.send(json.dumps(msg))
    return json.loads(ws.recv())

cdp("Page.enable")
cdp("Runtime.enable")

# Check state
r = cdp("Runtime.evaluate", {"expression": "typeof ForceGraph !== 'undefined'", "returnByValue": True})
print("ForceGraph:", r.get("result",{}).get("result",{}).get("value"))

r = cdp("Runtime.evaluate", {"expression": "typeof D !== 'undefined' && D !== null", "returnByValue": True})
print("D loaded:", r.get("result",{}).get("result",{}).get("value"))

# Wait for render
time.sleep(10)

# Capture
r = cdp("Page.captureScreenshot", {"format": "png"})
ws.close()

if "result" in r and "data" in r["result"]:
    img = base64.b64decode(r["result"]["data"])
    with open("/tmp/graph.png", "wb") as f:
        f.write(img)
    print(f"Screenshot: {len(img)} bytes")

chrome.terminate()
chrome.wait()
```

## Key flags

- `--remote-allow-origins=*` — required for websocket connections from non-Chrome clients
- `about:blank` as initial URL — prevents Chrome from loading the target page before CDP attaches, avoiding race conditions
- `PUT /json/new?<url>` — creates a new tab with the target URL; Chrome navigates to it

## Runtime inspection via CDP

Use `Runtime.evaluate` to check if libraries, data, and the graph object are actually present:

```python
# Check ForceGraph library loaded
cdp("Runtime.evaluate", {"expression": "typeof ForceGraph !== 'undefined'", "returnByValue": True})

# Check data loaded
cdp("Runtime.evaluate", {"expression": "typeof D !== 'undefined' && D !== null", "returnByValue": True})

# Check graph object created
cdp("Runtime.evaluate", {"expression": "typeof graph !== 'undefined' && graph !== null", "returnByValue": True})

# Manually trigger rebuild
cdp("Runtime.evaluate", {"expression": "if(typeof rebuildGraph==='function' && D) { rebuildGraph(); }"})

# Get console errors
cdp("Runtime.evaluate", {"expression": "console.error('check')"})
```

## Xvfb headful mode (for WebGL/Canvas)

If the headless canvas renders blank but you suspect WebGL or GPU-accelerated canvas is the issue, run Chrome under a virtual framebuffer:

```bash
# Start Xvfb
Xvfb :99 -screen 0 1920x1080x24 &
DISPLAY=:99 google-chrome-stable --no-sandbox [--screenshot=...] <url>
```

Note: `xvfb-run` wraps both steps. Chrome may hang on heavy JS pages (500KB+ inline data + tag edge O(n²) computation) because Xvfb + GPU fallback is slower than headless mode. Use headless + CDP for reliable results.

## Why --screenshot often fails for ForceGraph

Chrome's `--screenshot` flag captures the page immediately after the `load` event fires. ForceGraph initialization happens in the following timeline:

1. `load` event fires (CDN script + inline data parsed)
2. JS destructures data, builds tag index, calls `rebuildGraph()`
3. ForceGraph creates canvas, starts `warmupTicks(100)` + `cooldownTicks(30)` simulation
4. Canvas renders at first `requestAnimationFrame` after `cooldownTicks` completes

Steps 2-4 take 2-10 seconds depending on data size. `--screenshot` captures before step 2 completes.

The `--virtual-time-budget` flag helps but also throttles async operations — CDN fetches count against the budget. At 20-30s budget, CDN load + JS parse + simulation settle all must fit, which is tight for 500KB+ inline data with 600+ nodes.
