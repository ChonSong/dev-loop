# tmpfs Overflow Recovery — TrueNAS SCALE

## The Failure Chain

```
catalog.sync (Git clone to /var/run/middleware/ix-apps/catalogs) fails
  → journald flooded with error messages
    → /run (tmpfs, a few KB) fills up completely
      → pututline() fails (can't write /var/log/wtmp)
        → API logins fail with "No space left on device"
          → SMB service crashes or becomes unresponsive
            → Everything cascades
```

## Symptoms

- API login returns: `[EFAULT] Login with credentials failed: pututline() failed with error: No space left on device`
- WebSocket connect succeeds but login fails
- Port 445 (SMB) shows CLOSED or refuses connections
- `df -h` on boot pool shows plenty of space (the issue is tmpfs, not ZFS)

## Recovery Procedure

### Step 1: Fix the trigger (catalog sync)

```python
# Via tn_ws.py — must call with NO params
python3 /tmp/tn_ws.py 'catalog.sync' '[]'
```

**Important:** Calling with a label argument fails with "Too many arguments (expected 0, found 1)". The correct signature takes zero arguments.

### Step 2: Restart SMB service

```python
python3 /tmp/tn_ws.py 'service.restart' '["cifs"]'
```

### Step 3: Verify

```bash
# Check port is open
echo > /dev/tcp/192.168.1.102/445

# Test SMB access
# Via smbclient (if installed) or smbprotocol (Python)
```

## Prevention

The catalog sync is the most common trigger. Once it succeeds, journald stops getting flooded. If the issue recurs, the catalog sync may have failed again — re-run step 1.

## Tools Reference

- `tn_ws.py` — Generic TrueNAS WebSocket API client (in /tmp after setup)
- `tn_api.sh` — REST API wrapper (less reliable for writes)
- `truenas-mcp` binary — MCP server with 48+ tools (requires Hermes MCP client)

## WebSocket Protocol Notes

TrueNAS middleware WebSocket at `wss://<host>:443/websocket`:

1. **Connect:** `{"msg": "connect", "version": "1", "support": ["1"]}`  
   → Response: `{"msg": "connected", "session": "..."}`
   
2. **Authenticate:** `{"id": "1", "msg": "method", "method": "auth.login_with_api_key", "params": ["<key>"]}`  
   → Response: `{"msg": "result", "id": "1", "result": true}`
   
3. **Call method:** `{"id": "2", "msg": "method", "method": "<service.method>", "params": [...]}`  
   → Response: `{"msg": "result", "id": "2", "result": <data>}`

**Critical:** `version` MUST be a JSON string `"1"`, not integer `1`. The Go binary (gorilla/websocket + WriteJSON) sends it as string; Python's `json.dumps({"version": 1})` sends integer and gets rejected.

## Useful API Methods

| Category | Methods |
|----------|---------|
| Auth | `auth.login_with_api_key(key)` |
| SMB config | `smb.update({fields})` — set smb_options, guest, etc. |
| SMB shares | `sharing.smb.query([])`, `sharing.smb.create({})`, `sharing.smb.update(id, {})` |
| Users | `user.create({...})`, `user.query([])` — home must be /var/empty or /mnt/... |
| Datasets | `pool.dataset.query([])`, `pool.dataset.create({...})` |
| Filesystem | `filesystem.stat(path)`, `filesystem.statfs(path)`, `filesystem.setacl({path: {acl, options}})` |
| Boot | `boot.query([])`, `boot.get_state([])`, `boot.environment.query([])` |
| Services | `service.query([])`, `service.start(name)`, `service.stop(name)`, `service.restart(name)` |
| System | `system.info([])`, `disk.query([])` |
| Catalog | `catalog.sync([])` — no params |
| Jobs | `core.get_jobs([[["id", "=", N]]])` |
| Tunables | `tunable.create({type, var, value, enabled, comment})` |
