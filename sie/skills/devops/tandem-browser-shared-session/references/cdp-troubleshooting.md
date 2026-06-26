# CDP Troubleshooting Reference

Commands used during initial setup of the Electron remote debugging session.

## Verify Electron CDP is Running

```bash
# Check Electron is alive with CDP
curl -s http://127.0.0.1:9222/json/version | python3 -c "import sys,json; d=json.load(sys.stdin); print('Browser:', d.get('Browser','?')); print('CDP version:', d.get('Protocol-Version','?'))"
```

## List All Page Targets

```bash
curl -s http://127.0.0.1:9222/json | python3 -c "
import sys, json
targets = json.load(sys.stdin)
for t in targets:
    ttype = t.get('type','?')
    url = t.get('url','?')[:100]
    title = t.get('title','?')[:60]
    print(f'  [{ttype:8s}] {title:50s} {url}')
print(f'\nTotal: {len(targets)} targets')
```

## Navigate via Raw CDP (no viewer needed)

Use a WebSocket client (Python example):

```python
import json, websocket
ws = websocket.create_conn("ws://127.0.0.1:9222/devtools/page/<TARGET_ID>")
ws.send(json.dumps({"id":1,"method":"Page.enable"}))
ws.recv()
ws.send(json.dumps({"id":2,"method":"Page.navigate","params":{"url":"https://example.com"}}))
ws.recv()
ws.close()
```

## Check Ports

```bash
# What's on CDP port?
ss -tlnp | grep 9222
# What's on viewer port?
ss -tlnp | grep 3099
```

## Kill Stale Processes

```bash
# Kill everything on both ports
lsof -ti :9222 | xargs -r kill
lsof -ti :3099 | xargs -r kill
# Verify free
lsof -ti :9222 || echo "9222 free"
lsof -ti :3099 || echo "3099 free"
```

## Viewer Logs

```bash
tail -20 /tmp/tandem-debug.log     # Electron startup
tail -20 /tmp/electron-viewer.log   # Viewer connection
```

## Unsupported CDP Methods (Electron)

These returned "Not supported":
- `Target.createTarget` — cannot create hidden background pages
