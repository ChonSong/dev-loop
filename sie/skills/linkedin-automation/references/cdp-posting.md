# CDP Posting Reference

Concrete patterns for posting to LinkedIn via Chrome DevTools Protocol. Updated based on extensive session testing (2026-05-31).

## Connection Pattern

```python
import json, websocket, urllib.request, time

CDP_PORT = 9222

def connect():
    targets = json.loads(urllib.request.urlopen(f"http://localhost:{CDP_PORT}/json/list", timeout=5).read())
    li = next((t for t in targets if "linkedin.com" in t.get("url", "")), None)
    if not li:
        req = urllib.request.Request(f"http://localhost:{CDP_PORT}/json/new?url=https://www.linkedin.com/feed/", method="PUT")
        li = json.loads(urllib.request.urlopen(req, timeout=10).read())
        time.sleep(5)
    ws = websocket.create_connection(li["webSocketDebuggerUrl"], timeout=60)
    ws.settimeout(30)
    return ws, li
```

## ⚠️ Page.navigate Is Unreliable — Do NOT Use in Production

`Page.navigate` blocks until the page fully loads. LinkedIn's feed takes 30-60+ seconds, causing WebSocket timeouts at every timeout tier tested (30s, 60s, 120s, 180s).

**Even fire-and-forget fails** because after reconnecting, `Runtime.evaluate` blocks for 30s+ waiting for the JS context to initialize.

**SOLUTION:** Assume the tab is already on the LinkedIn feed. Sean's Chrome is always open with LinkedIn loaded. Just connect and act on the current page state. If you must navigate, expect the script to take 90-120+ seconds and handle it via `nohup` on the host (not SSH).

## Element Finding (React UI)

LinkedIn uses dynamically-hashed CSS class names. **Never search by class.**

```python
# Find the "Start a post" composer
pos = ev('var el=document.evaluate("//*[text()=\'Start a post\']",document,null,XPathResult.FIRST_ORDERED_NODE_TYPE,null).singleNodeValue;if(!el)\'nf\';else{var r=el.parentElement.getBoundingClientRect();Math.round(r.top)+","+Math.round(r.left)+","+Math.round(r.width)+","+Math.round(r.height)}')

# Parse position (getBoundingClientRect returns floats!)
pp = pos.split(",")
t, l, w, h = int(float(pp[0])), int(float(pp[1])), int(float(pp[2])), int(float(pp[3]))
cx, cy = l + w // 2, t + h // 2  # center of element
```

## Click Pattern

Use CDP mouse events (not `element.click()` — React synthetic events may not fire):

```python
def click(ws, x, y):
    cdp(ws, "Input.dispatchMouseEvent", {"type": "mousePressed", "x": x, "y": y, "button": "left", "clickCount": 1, "buttons": 1})
    time.sleep(0.1)
    cdp(ws, "Input.dispatchMouseEvent", {"type": "mouseReleased", "x": x, "y": y, "button": "left", "clickCount": 1, "buttons": 0})
```

## Type Pattern

```python
def type_text(ws, text, delay=0.04):
    for ch in text:
        cdp(ws, "Input.dispatchKeyEvent", {"type": "keyDown", "key": ch, "text": ch})
        cdp(ws, "Input.dispatchKeyEvent", {"type": "char", "text": ch, "key": ch})
        cdp(ws, "Input.dispatchKeyEvent", {"type": "keyUp", "key": ch, "text": ch})
        time.sleep(delay)
```

## Submit Pattern (Tab to Post Button)

```python
for _ in range(20):
    cdp(ws, "Input.dispatchKeyEvent", {"type": "keyDown", "key": "Tab", "code": "Tab", "windowsVirtualKeyCode": 9})
    cdp(ws, "Input.dispatchKeyEvent", {"type": "keyUp", "key": "Tab", "code": "Tab", "windowsVirtualKeyCode": 9})
    time.sleep(0.3)
    f = ev("var e=document.activeElement;(e.innerText||'').trim().substring(0,40)+'|'+e.tagName")
    if "post" in str(f).lower() or "share" in str(f).lower():
        cdp(ws, "Input.dispatchKeyEvent", {"type": "keyDown", "key": "Enter", "code": "Enter", "windowsVirtualKeyCode": 13})
        cdp(ws, "Input.dispatchKeyEvent", {"type": "keyUp", "key": "Enter", "code": "Enter", "windowsVirtualKeyCode": 13})
        break
```

## Chrome Launch Command

```bash
pkill -f "google-chrome"
sleep 2
rm -f /home/sean/.config/google-chrome/SingletonLock
nohup /opt/google/chrome/chrome \
  --remote-debugging-port=9222 \
  --remote-allow-origins=* \
  --user-data-dir=/home/sean/.config/google-chrome/Default \
  > /tmp/chrome-debug.log 2>&1 &
sleep 5
# Verify: curl http://localhost:9222/json/version
```

**Critical flags:**
- `--remote-debugging-port=9222` — enables CDP
- `--remote-allow-origins=*` — without this, WebSocket gets HTTP 403

## Running Long Scripts on Host

SSH sessions timeout at 60s. Long-running LinkedIn scripts MUST use `nohup`:

```bash
# On host:
nohup python3 /tmp/linkedin-post-runner.py > /tmp/li-run.log 2>&1 &
# Then check later:
cat /tmp/li-run.log
```

## Module Import Gotcha

The post runner imports `linkedin_browser.py` (underscore), not `linkedin-browser.py` (hyphen). After updating `linkedin-browser.py`, always copy:

```bash
cp /tmp/linkedin-browser.py /tmp/linkedin_browser.py
```
