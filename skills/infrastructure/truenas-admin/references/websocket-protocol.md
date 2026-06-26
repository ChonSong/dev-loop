# TrueNAS WebSocket Protocol Reference

The TrueNAS middleware exposes a custom JSON-based WebSocket protocol on `wss://<host>:443/websocket`.

## Full Connection Flow

```python
import json, websocket, ssl

ws = websocket.create_connection(
    'wss://192.168.1.102:443/websocket', timeout=15,
    sslopt={'cert_reqs': ssl.CERT_NONE}
)
ws.settimeout(30)

# Step 1: Connect — version MUST be string "1"
ws.send(json.dumps({"msg": "connect", "version": "1", "support": ["1"]}))
resp = json.loads(ws.recv())
assert resp["msg"] == "connected", f"Connect failed: {resp}"
session = resp.get("session")

# Step 2: Authenticate with API key
ws.send(json.dumps({
    "id": "1", "msg": "method", "method": "auth.login_with_api_key",
    "params": [api_key]
}))
resp = json.loads(ws.recv())
assert resp.get("result") is True, f"Login failed: {resp}"

# Step 3: Call any middleware method
def call(method, params):
    msg_id = str(int(time.time() * 1000) % 100000)
    ws.send(json.dumps({
        "id": msg_id, "msg": "method", "method": method, "params": params
    }))
    resp = json.loads(ws.recv())
    if resp.get("msg") == "failed" or resp.get("error"):
        return {"error": resp.get("error", resp)}
    return resp.get("result")
```

## Version String Gotcha (Critical)

The `version` field in the connect message MUST be a JSON **string** `"1"`, not the integer `1`. Python's `json.dumps({"version": 1})` produces `{"version": 1}` which TrueNAS rejects with `{"msg":"failed"}`.

## REST API (Alternate)

Available at `https://<host>/api/v2.0/<path>` with `Authorization: Bearer <api_key>` header.

```bash
# GET query
curl -sk -H "Authorization: Bearer $KEY" "https://host/api/v2.0/pool"

# PUT update
curl -sk -X PUT -H "Content-Type: application/json" \
  -H "Authorization: Bearer $KEY" \
  -d '{"key": "value"}' \
  "https://host/api/v2.0/smb"
```

## Common Service Methods

| Method | Purpose |
|--------|---------|
| `system.info` | System version, hostname, uptime |
| `pool.query` | Storage pool status and health |
| `pool.dataset.query` | Dataset list with capacity |
| `sharing.smb.query` | List SMB shares |
| `sharing.smb.create` | Create SMB share |
| `sharing.smb.update` | Update SMB share (by ID) |
| `smb.update` | Update global SMB service config |
| `user.create` | Create user account |
| `user.query` | List users |
| `filesystem.setacl` | Set dataset ACL (NFSv4 format) |
| `filesystem.stat` | Get file/directory metadata |
| `filesystem.setperm` | Set POSIX permissions (returns job ID) |
| `service.start/stop/restart` | Control system services |
| `service.query` | List services and their state |
| `app.query` | List installed apps |
| `app.available` | List catalog apps |
| `core.get_jobs` | Check job status |

## Service Names for service.* Methods

- `cifs` — SMB/CIFS
- `ssh` — SSH server
- `nfs` — NFS
- `ftp` — FTP
- `snmp` — SNMP
- `iscsitarget` — iSCSI
- `ups` — UPS
- `nvmet` — NVMe-oF
