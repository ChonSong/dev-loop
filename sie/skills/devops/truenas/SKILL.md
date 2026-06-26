---
name: truenas
description: Manage TrueNAS SCALE via MCP and WebSocket API — setup, SMB shares, troubleshooting
version: 1.0.0
author: Hermes Agent
platforms: [linux]
---

# TrueNAS Management

Manage a TrueNAS SCALE system (typically in VirtualBox VM) through the Hermes agent. Two approaches:

1. **MCP server** (`truenas-mcp` binary) — connects via WebSocket, 48+ tools auto-discovered as `mcp_truenas_*`
2. **Direct WebSocket API** (`tn_ws.py`) — for operations the MCP server doesn't expose

## MCP Server Setup

Download the latest `truenas-mcp-linux-amd64.tar.gz` from GitHub releases, place on PATH, and add to Hermes `config.yaml`:

```yaml
mcp_servers:
  truenas:
    command: /path/to/truenas-mcp
    args: ["--truenas-url", "192.168.1.102", "--api-key", "${TRUENAS_API_KEY}"]
    timeout: 120
    connect_timeout: 30
```

The binary handles TrueNAS self-signed certs automatically.

**Important:** The `mcp_servers` config MUST be in the config file that `get_hermes_home() / "config.yaml"` points to (use `from hermes_cli.config import get_hermes_home` to find it). After adding, either restart Hermes or call `discover_mcp_tools()` to connect.

## Available MCP Tools (v0.2.0)

- System: `system_info`, `system_health`, `system_reboot`
- Storage: `query_pools`, `query_datasets`, `query_snapshots`, `create_dataset`, `query_shares`
- SMB/NFS: `create_smb_share`, `create_nfs_share`
- Apps: `search_app_catalog`, `install_app`, `upgrade_app`, `start_app`, `stop_app`, `delete_app`
- Maintenance: `check_updates`, `download_update`, `apply_update`, `run_scrub`, `create_scrub_schedule`
- Monitoring: `get_system_metrics`, `get_disk_metrics`, `get_network_metrics`, `get_arc_metrics`, `get_ups_metrics`, `analyze_capacity`
- Alerts: `list_alerts`, `dismiss_alert`, `restore_alert`
- VMs: `query_vms`
- Directory Services: `configure_directory_service`, `query_directory_services`, `leave_directory_service`, `get_directory_service_status`
- Boot: `query_boot_environments`, `delete_boot_environment`, `get_current_boot_environment`
- Jobs: `tasks_get`, `tasks_list`, `query_jobs`

## Direct WebSocket API (`tn_ws.py`)

For operations not covered by MCP tools (user creation, SMB config updates, shell commands), use the WebSocket API directly.

**Key protocol quirk:** The `version` field in the connect message MUST be a **string** `"1"`, not integer `1`:

```python
# CORRECT — TrueNAS rejects integer
ws.send(json.dumps({"msg": "connect", "version": "1", "support": ["1"]}))
```

**Authentication pattern:**
```python
# After connect response, login
ws.send(json.dumps({
    "id": "1", "msg": "method", "method": "auth.login_with_api_key",
    "params": [API_KEY]
}))
# Check: resp["result"] should be True
```

## Creating SMB Shares with Password Access

1. Create dataset: `create_dataset("pool/public", "FILESYSTEM", "SMB", "LZ4", "NFSV4")`
2. Create SMB share: `create_smb_share(name, path, purpose="DEFAULT_SHARE", ...)`
3. Create user with SMB enabled via WebSocket API:
   ```
   user.create({"username": "shared", "password": "...", "smb": true, "home": "/var/empty"})
   ```
4. Set ACL on dataset:
   ```
   filesystem.setacl({"/mnt/pool/public": {"acl": [...], "options": {...}})
   ```

## SMB Guest Access (TrueNAS SCALE 25.x)

TrueNAS SCALE 25.x has deprecated per-share `guestok`. Instead:
- Set SMB service option: `smb_options: "map to guest = Bad User"`
- Configure ACL with `everyone@` FULL_CONTROL
- Guest users map to system `nobody` account
- **Limitation:** Guest access requires `server signing = disabled` in smb_options, and some SMB clients (smbprotocol, Python) may still fail with signing errors. Windows clients handle this better.

## Recovery from tmpfs Overflow

See `references/tmpfs-overflow.md` for the full diagnostic and recovery procedure.

## Scripts

- `scripts/tn-ws.py` — reusable TrueNAS WebSocket API client. Call any method: `python3 tn-ws.py 'catalog.sync' '[]'`


## Pitfalls

- **Config file location:** MCP servers must be in `get_hermes_home() / "config.yaml"`, NOT in a nested `.hermes/home/.hermes/` config. Check with `from hermes_cli.config import get_hermes_home`.
- **API key placement:** MCP server args expose the API key in plaintext in config.yaml. Move to env var for production.
- **REST API vs WebSocket:** The REST API (`/api/v2.0/...`) may return 500 errors for write operations; use the WebSocket API instead.
- **Binary path:** The MCP subprocess inherits a filtered environment. Use absolute paths for the command.
- **catalog.sync:** Calling with no params succeeds; calling with a label fails with "Too many arguments".
