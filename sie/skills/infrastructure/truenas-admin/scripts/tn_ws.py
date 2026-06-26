#!/usr/bin/env python3
"""
TrueNAS WebSocket API client — calls any middleware method.
Usage: python3 tn_ws.py <method> [params_json]
Example: python3 tn_ws.py system.info []
         python3 tn_ws.py user.create '[{"username":"test","password":"test1","smb":true}]'
         python3 tn_ws.py pool.query []
"""
import json, websocket, ssl, sys, time

# Edit these for your TrueNAS host
TRUENAS_URL = "192.168.1.102"
API_KEY = "your-api-key-here"

ws = websocket.create_connection(
    f'wss://{TRUENAS_URL}:443/websocket', timeout=15,
    sslopt={'cert_reqs': ssl.CERT_NONE}
)
ws.settimeout(30)

# Step 1: connect — version MUST be string "1" not integer 1
ws.send(json.dumps({"msg": "connect", "version": "1", "support": ["1"]}))
resp = json.loads(ws.recv())
assert resp["msg"] == "connected", f"Connect failed: {resp}"
session = resp.get("session", "")
print(f"Session: {session[:20]}", file=sys.stderr)

# Step 2: login
ws.send(json.dumps({
    "id": "1", "msg": "method", "method": "auth.login_with_api_key",
    "params": [API_KEY]
}))
resp = json.loads(ws.recv())
assert resp.get("result") is True, f"Login failed: {resp}"
print("Auth: OK", file=sys.stderr)

def call(method, params):
    msg_id = str(int(time.time() * 1000) % 100000)
    ws.send(json.dumps({
        "id": msg_id, "msg": "method", "method": method, "params": params
    }))
    resp = json.loads(ws.recv())
    if resp.get("msg") == "failed" or resp.get("error"):
        return {"error": resp.get("error", resp)}
    return resp.get("result")

if len(sys.argv) >= 2:
    method = sys.argv[1]
    params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else []
    result = call(method, params)
    print(json.dumps(result, indent=2, default=str)[:5000])
else:
    print("Usage: tn_ws.py <method> [params_json]", file=sys.stderr)
    print("Example: tn_ws.py system.info []", file=sys.stderr)

ws.close()
