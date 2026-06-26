#!/usr/bin/env python3
"""
TrueNAS WebSocket API CLI — call any middleware method.
Usage:
    tn-ws-call.py smb.update '{"smb_options": "map to guest = Bad User"}'
    tn-ws-call.py sharing.smb.query  '[]'
    tn-ws-call.py user.create '{"username":"x","password":"p","smb":true,"group_create":true,"home":"/var/empty","shell":"/usr/sbin/nologin"}'
    tn-ws-call.py pool.query '[]'
    tn-ws-call.py core.get_jobs '[[["id","=",302]]]'
    tn-ws-call.py service.restart '["cifs"]'
"""
import json, os, sys, time, ssl, websocket

API_KEY = os.environ.get("TRUENAS_API_KEY")
HOST = os.environ.get("TRUENAS_HOST", "192.168.1.102")

if not API_KEY:
    print("FATAL: Set TRUENAS_API_KEY env var", file=sys.stderr)
    sys.exit(1)

ws = websocket.create_connection(
    f"wss://{HOST}:443/websocket", timeout=15,
    sslopt={"cert_reqs": ssl.CERT_NONE})
ws.settimeout(30)

# Connect — version AS STRING "1" (NOT integer 1)
ws.send(json.dumps({"msg": "connect", "version": "1", "support": ["1"]}))
resp = json.loads(ws.recv())
assert resp["msg"] == "connected", f"Connect failed: {resp}"

# Login
ws.send(json.dumps({
    "id": "1", "msg": "method", "method": "auth.login_with_api_key",
    "params": [API_KEY]}))
resp = json.loads(ws.recv())
assert resp.get("result") is True, f"Login failed: {resp.get('error')}"

def call(method, params):
    mid = str(int(time.time() * 1000) % 100000)
    ws.send(json.dumps({"id": mid, "msg": "method", "method": method, "params": params}))
    resp = json.loads(ws.recv())
    if resp.get("msg") == "failed" or resp.get("error"):
        return {"error": resp.get("error", resp)}
    return resp.get("result")

if len(sys.argv) < 2:
    print("Usage: tn-ws-call.py <method> [params_json]", file=sys.stderr)
    sys.exit(1)

method = sys.argv[1]
params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else []
result = call(method, params)
print(json.dumps(result, indent=2, default=str)[:10000])
ws.close()
