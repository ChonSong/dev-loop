---
name: truenas-admin
description: "Administer TrueNAS SCALE systems via MCP tools, WebSocket API, and REST API — storage, shares, users, services, and container hosting"
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [truenas, nas, storage, smb, nfs, zfs, infrastructure]
    related_skills: [mcp/native-mcp]
---

# TrueNAS Administration

## When to Use

Load this skill when the user asks you to:
- Check or configure TrueNAS system state (pools, datasets, shares)
- Create, update, or troubleshoot SMB / NFS shares
- Manage TrueNAS users and permissions
- Install or update TrueNAS apps
- Configure directory services (AD, LDAP, IPA)
- Check system health, alerts, or performance metrics
- Plan to run workloads on TrueNAS (container hosting, VM setup)

## Prerequisites

- **truenas-mcp** binary installed and configured as an MCP server under `mcp_servers` in Hermes config (see `mcp/native-mcp` skill)
- A TrueNAS API key with sufficient permissions (FULL_ADMIN recommended for initial setup)
- Network access to the TrueNAS host (default ports: 443 for WebSocket/REST, 445 for SMB)

## Tools Available

### Via MCP Server (truenas-mcp)
Tools are prefixed `mcp_truenas_*` and include: system info/health/alerts, pool/dataset/snapshot management, SMB/NFS share CRUD, app catalog search/install/upgrade, VM management, scrub schedules, boot environments, directory services.

### Via Direct API (for operations not covered by MCP tools)
Use the WebSocket API (`wss://<host>:443/websocket`) for arbitrary TrueNAS middleware calls not exposed by truenas-mcp (e.g., `smb.update`, `user.create`, `filesystem.setacl`, `service.*`).

## TrueNAS WebSocket Protocol (Critical Details)

The TrueNAS middleware uses a custom JSON-based WebSocket protocol. Key protocol details:

### Connect
```json
// Send (CRITICAL: version MUST be string "1", NOT integer 1)
{"msg": "connect", "version": "1", "support": ["1"]}
// Response on success
{"msg": "connected", "session": "uuid-here"}
// Response on failure
{"msg": "failed", "version": "1"}
```

**⚠️ The `version` field must be the string `"1"`, not the integer `1`.** The Python websocket client's `json.dumps({"version": 1})` produces `{"version": 1}` which TrueNAS rejects with `{"msg":"failed"}`. This is the single most common connection failure.

### Authentication
```python
{"id": "1", "msg": "method", "method": "auth.login_with_api_key", "params": [api_key]}
# Response: {"msg": "result", "result": true} on success
```

### Method Calls
```python
{"id": str(msg_id), "msg": "method", "method": "<service.method>", "params": [...]}
# Response: {"msg": "result", "result": <data>, "id": "<msg_id>"}
```

### REST API (Alternative)
Available at `https://<host>/api/v2.0/<path>` with `Authorization: Bearer <api_key>` header. Useful for GET queries but POST/PUT writes may fail on low-resource VMs.

## Service Management

TrueNAS SCALE services are managed via the `service.*` API. **Verbs must be uppercase strings** (`"START"`, `"STOP"`, `"RESTART"`, `"RELOAD"`).

```python
# Start SSH
ws_call("service.control", ["START", "ssh"])   # returns job ID

# Restart SMB
ws_call("service.control", ["RESTART", "cifs"])
```

Available services: `cifs` (SMB), `ssh`, `nfs`, `ftp`, `snmp`, `iscsitarget`, `ups`, `nvmet`.

Note: Docker and containerd do NOT appear in the middleware service list — use systemd directly via SSH instead.

## SSH Access via API

If SSH is disabled and no key is configured, you can enable it entirely through the API:

```python
# 1. Start the SSH service
ws_call("service.control", ["START", "ssh"])

# 2. Inject the container's SSH public key into root's authorized_keys
my_public_key = "ssh-ed25519 AAA... keyname"
ws_call("user.update", [1, {"sshpubkey": my_public_key}])

# 3. Wait a moment, then SSH in
ssh -i /path/to/private_key root@<truenas-host>
```

## Docker on TrueNAS SCALE

TrueNAS SCALE 25.x ships with Docker installed but **disabled** — the service unit is `inactive (dead)` and `disabled` at boot, managed via systemd, not through the middleware service list.

```bash
# On the TrueNAS host (via SSH):
systemctl start docker         # Start Docker daemon
systemctl enable docker        # Enable at boot
docker info                    # Verify: overlay2 driver, /var/lib/docker on boot pool
```

Docker root is `/var/lib/docker` on the boot pool. For production, reconfigure via `/etc/docker/daemon.json` to use a data pool.

### App Deployment via API (what works and what doesn't)

The `app.create` middleware method exists but has strict requirements:

- ✅ Accepts `catalog_app` — a pre-packaged app name from the TrueNAS catalog (Plex, MinIO, etc.)
- ✅ Returns a job ID — track with `core.get_jobs`
- ❌ **Does NOT accept** `image`, `name`, or raw Docker image references — `app_create.image: Extra inputs are not permitted`
- ❌ **Does NOT accept** arbitrary `app_name` — requires `catalog_app` from the catalog

```python
# List available catalog apps
ws_call("app.available", [])

# Install a catalog app
ws_call("app.create", [{
    "app_name": "my-instance",
    "catalog_app": "plex",      # from app.available
    "version": "1.3.10",
    "train": "stable",
    "values": {...}
}])
```

To run arbitrary containers, use raw Docker via SSH instead of the app API.

## tmpfs Overflow Recovery

TrueNAS SCALE uses tmpfs for `/run`, which can overflow when a system service floods journald with errors. This manifests as:

- `pututline() failed with error: No space left on device` on API login
- REST API writes returning HTTP 500
- SMB service crashing or refusing connections
- SSH becoming unavailable

**Root cause chain:**

```
Failing system service (e.g., catalog.sync cloning a git repo to /var/run) →
Floods journald with error messages on /run/log/journal →
/run tmpfs fills up (small, usually KB-MB capacity) →
pututline() can't write to /run/utmp →
All new logins fail → services cascade into failures
```

**Recovery:**

```python
# Step 1: Fix the flooding service — catalog.sync with no params
ws_call("catalog.sync", [])     # NOT: catalog.sync("TRUENAS", {}) which errors

# Step 2: Restart crashed services
ws_call("service.restart", ["cifs"])   # SMB
ws_call("service.control", ["START", "ssh"])   # SSH if needed

# Step 3: Verify
ws_call("system.info", [])
```

## Common Administration Tasks

### SMB Share with Simple Password (Preferred for TrueNAS SCALE 25.x)

TrueNAS SCALE 25.x removed the per-share `guestok` parameter. Guest access is instead controlled through:
1. `smb_options: "map to guest = Bad User"` in the SMB service config
2. `everyone@` ACL entries on the shared dataset
3. The global SMB guest account (`guest: "nobody"`)

**Strategy: Create a dedicated user with a simple password instead of relying on guest access,** which is blocked by TrueNAS SCALE's signing requirements.

```python
# Create user
ws_call("user.create", [{
    "username": "shared",
    "full_name": "Shared Access", 
    "password": "shared1",
    "group_create": True,
    "smb": True,
    "shell": "/usr/sbin/nologin",
    "home": "/var/empty",
    "home_create": False,
    "locked": False
}])
```

Then set dataset ACL to grant that user access:
```python
ws_call("filesystem.setacl", [{"/mnt/pool/share": {
    "acl": [
        {"tag": "owner@", "type": "ALLOW", "perms": {"BASIC": "FULL_CONTROL"}, "flags": {"BASIC": "INHERIT"}},
        {"tag": "group@", "type": "ALLOW", "perms": {"BASIC": "FULL_CONTROL"}, "flags": {"BASIC": "INHERIT"}},
        {"tag": "everyone@", "type": "ALLOW", "perms": {"BASIC": "FULL_CONTROL"}, "flags": {"BASIC": "INHERIT"}},
        {"tag": "USER", "type": "ALLOW", "who": "shared", "perms": {"BASIC": "FULL_CONTROL"}, "flags": {"BASIC": "INHERIT"}}
    ],
    "options": {"recursive": False, "traverse": False}
}}])
```

If guest access must be used, enable `map to guest = Bad User` in SMB options and restart the SMB service. Note that modern SMB clients (Windows 10+, smbprotocol) may reject guest sessions that can't sign.

### SMB Service Configuration
```python
# Enable guest mapping
ws_call("smb.update", [{"smb_options": "map to guest = Bad User\nserver signing = disabled"}])
# Restart to apply
ws_call("service.restart", ["cifs"])
```

### User Management
- New users need `smb: true` to get an SMB password hash
- Home directory must start with `/mnt` or be `/var/empty`
- Set `shell: "/usr/sbin/nologin"` for service accounts

## Pitfalls

### TrueNAS VM Disk Space
TrueNAS SCALE running in VirtualBox with a single disk can run out of space on the root dataset even when the data pool shows plenty free. This manifests as:
- REST API writes returning HTTP 500
- `pututline() failed with error: No space left on device` on API login
- App installation or user creation silently failing

**Fix:** Check System Settings → Boot → delete old boot environments. If that's insufficient, expand the VirtualBox disk and grow the pool.

### REST API Writes vs WebSocket
The REST API (PUT/POST on `/api/v2.0/`) may return 500 errors on write operations when the WebSocket middleware method succeeds. For any write operation that fails via REST, try the WebSocket protocol instead.

### MCP Binary Path in Filtered Environment
When configuring `truenas-mcp` (or any stdio MCP server) in `mcp_servers`, the `command` path must be resolvable in the MCP subprocess's filtered environment. The subprocess inherits only `PATH`, `HOME`, `USER`, `LANG`, `LC_ALL`, `TERM`, `SHELL`, `TMPDIR`, and `XDG_*` variables plus any `env` overrides. Use an **absolute path** to the binary to avoid resolution failures.

## Reference Files

- `references/websocket-protocol.md` — complete TrueNAS WebSocket protocol reference and the `tn_ws.py` wrapper script pattern
- `references/smb-guest-access.md` — detailed SMB guest access troubleshooting
- `scripts/tn_ws.py` — reusable TrueNAS WebSocket API client script
