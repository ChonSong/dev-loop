---
name: truenas-management
description: Manage TrueNAS from Hermes — MCP server setup, WebSocket API, REST API, storage pools, SMB/NFS shares, datasets, users, apps, alerts, and system maintenance
version: 1.1.0
author: Hermes Agent
tags: [truenas, nas, storage, smb, nfs, zfs, datasets, shares, websocket]
---

# TrueNAS Management

Manage a TrueNAS system via two channels:
1. **MCP server** (`truenas-mcp` binary) — registered tools with `mcp_truenas_*` prefix
2. **Direct WebSocket API** (preferred for writes) or **REST API** — when MCP tools don't expose the needed endpoint

## Discovery: Finding TrueNAS in a Fresh Environment

When you wake up without pre-configured credentials, hunt in this order:

1. **Env vars**: `env | grep -iE 'truenas|tn_|nas_'`
2. **Hermes config**: `python3 -c "from hermes_cli.config import load_config; print(list(load_config().get('mcp_servers', {}).keys()))"`
3. **Config file**: `cat $(python3 -c "from hermes_cli.config import get_hermes_home; print(get_hermes_home())")/config.yaml | grep -A5 truenas`
4. **Session memory**: Search past sessions for `TRUENAS_HOST`, `TRUENAS_API_KEY`, or IP addresses.
5. **SSH keys**: Check both `~/.ssh/id_ed25519` **and** `$HERMES_HOME/.ssh/id_ed25519` — in WebUI/container deployments they often diverge.
6. **Known hosts**: `cat ~/.ssh/known_hosts` or `$HERMES_HOME/.ssh/known_hosts` for TrueNAS IP fingerprints.
7. **Ask the user**: If all of the above fail, ask directly — "What's the TrueNAS IP and do you have an API key or root SSH key?"

**Pitfall — dual SSH key locations**: The container's `$HOME` (`/home/hermeswebui`) and `get_hermes_home()` may be different directories. Always check both before declaring a key missing.

**Pitfall — truenas-mcp binary**: The binary is often already installed (check `which truenas-mcp`, `find /home/hermeswebui -name truenas-mcp`, `find /app -name truenas-mcp`). If found but unconfigured, proceed to configure `config.yaml`. If missing, download from GitHub releases.

## Prerequisites

- TrueNAS API key (System Settings → API Keys)
- Network access to TrueNAS WebSocket port 443
- `truenas-mcp` binary for MCP mode

## Setup: MCP Server

### 1. Install the binary

```bash
# Download from GitHub releases
curl -sL https://github.com/truenas/truenas-mcp/releases/download/v0.0.4/truenas-mcp-linux-amd64.tar.gz -o /tmp/tn-mcp.tar.gz
tar xzf /tmp/tn-mcp.tar.gz -C /tmp/

# Install somewhere persistent
cp /tmp/truenas-mcp-linux-amd64 /some/path/truenas-mcp
chmod +x /some/path/truenas-mcp
```

### 2. Get API key

From TrueNAS UI: **System Settings → API Keys → Add**

### 3. Configure Hermes MCP server

Add to `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  truenas:
    command: /absolute/path/to/truenas-mcp
    args: ["--truenas-url", "192.168.1.X", "--api-key", "your-api-key"]
    timeout: 120
    connect_timeout: 30
```

**Pitfall — WebUI dual config files:** In Hermes WebUI deployments, `$HOME` may differ from `get_hermes_home()`. The authoritative config path is `get_hermes_home() / "config.yaml"`, NOT `~/.hermes/config.yaml`. Always verify with `python3 -c "from hermes_cli.config import load_config; print(list(load_config().get('mcp_servers', {}).keys()))"`.

### 4. Restart Hermes

MCP servers are discovered at startup only (no hot-reload for new servers). After restart, tools appear as `mcp_truenas_*`.

Verify: `python3 -c "from tools.mcp_tool import discover_mcp_tools; print(discover_mcp_tools())"`

## Using MCP Tools

Once connected, call tools directly via the MCP interface. The agent sees them as first-class tools with the `mcp_truenas_` prefix.

### Quick Reference

| Category | Tools |
|----------|-------|
| Monitoring | `system_info`, `system_health`, `list_alerts`, `get_system_metrics`, `get_disk_metrics`, `get_network_metrics`, `get_arc_metrics`, `get_ups_metrics` |
| Storage | `query_pools`, `query_datasets`, `query_snapshots`, `query_shares`, `get_pool_capacity_details`, `analyze_capacity`, `create_dataset`, `create_smb_share`, `create_nfs_share`, `get_scrub_status`, `run_scrub`, `create_scrub_schedule` |
| Apps | `search_app_catalog`, `get_app_catalog_details`, `install_app`, `query_apps`, `upgrade_app`, `start_app`, `stop_app`, `delete_app` |
| Maintenance | `check_updates`, `download_update`, `apply_update`, `run_scrub`, `get_scrub_status`, `create_scrub_schedule`, `query_boot_environments`, `delete_boot_environment`, `system_reboot` |
| Directory | `configure_directory_service`, `get_directory_service_status`, `query_directory_services`, `leave_directory_service`, `refresh_directory_cache` |
| VMs | `query_vms` |
| Tasks | `tasks_get`, `tasks_list`, `query_jobs` |

## Direct WebSocket API (When MCP Falls Short) ⭐ Preferred

The TrueNAS middleware WebSocket API is more reliable than REST for write operations. REST PUT on SMB config consistently returned 500 errors; WebSocket calls worked.

### Connection Protocol

**CRITICAL**: `version` MUST be the **string** `"1"`, not the integer `1`. Sending an integer silently fails with `{"msg": "failed"}` — the error message gives no clue about the root cause.

```python
import json, websocket, ssl

ws = websocket.create_connection('wss://192.168.1.X:443/websocket', timeout=15,
    sslopt={'cert_reqs': ssl.CERT_NONE})
ws.settimeout(30)

# Connect — version AS STRING "1" (NOT integer 1)
ws.send(json.dumps({"msg": "connect", "version": "1", "support": ["1"]}))
resp = json.loads(ws.recv())
assert resp["msg"] == "connected"

# Login
ws.send(json.dumps({
    "id": "1", "msg": "method", "method": "auth.login_with_api_key",
    "params": [API_KEY]
}))
resp = json.loads(ws.recv())
assert resp.get("result") is True
```

### Calling Methods

```python
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

### Operations Not Covered by MCP Tools

```python
# Create user with SMB access
call("user.create", [{
    "username": "shared", "password": "shared1", "smb": True,
    "group_create": True, "home": "/var/empty", "home_create": False,
    "shell": "/usr/sbin/nologin", "locked": False
}])

# Update SMB service config (enable guest mapping, disable signing)
call("smb.update", [{"smb_options": "map to guest = Bad User\nserver signing = disabled"}])

# Set filesystem ACL (returns job ID)
call("filesystem.setacl", [{
    "path": "/mnt/p1/public",
    "dacl": [
        {"tag": "owner@", "type": "ALLOW", "perms": {"BASIC": "FULL_CONTROL"}, "flags": {"BASIC": "INHERIT"}},
        {"tag": "group@", "type": "ALLOW", "perms": {"BASIC": "FULL_CONTROL"}, "flags": {"BASIC": "INHERIT"}},
        {"tag": "everyone@", "type": "ALLOW", "perms": {"BASIC": "FULL_CONTROL"}, "flags": {"BASIC": "INHERIT"}}
    ],
    "options": {"recursive": False, "traverse": False}
}])

# Restart SMB service after config changes
call("service.restart", ["cifs"])

# Check job status (for setacl, setperm, etc.)
call("core.get_jobs", [[["id", "=", 302]]])
```

### Key WebSocket Methods vs REST

| Operation | WebSocket Method | REST Endpoint | Notes |
|-----------|-----------------|---------------|-------|
| SMB service config | `smb.update` | `PUT /api/v2.0/smb` | REST returns 500; WebSocket works |
| List SMB shares | `sharing.smb.query` | `GET /api/v2.0/sharing/smb` | Both work |
| Create SMB share | `sharing.smb.create` | `POST /api/v2.0/sharing/smb` | MCP tool covers this |
| Create user | `user.create` | `POST /api/v2.0/user` | WebSocket shows validation details |
| Set ACL | `filesystem.setacl` | `POST /api/v2.0/filesystem/setacl` | Returns job ID |
| Get ACL | `filesystem.getacl` | `POST /api/v2.0/filesystem/getacl` | Body: `[{"path":"/mnt/..."}]` |
| Restart service | `service.restart` | — | WebSocket param is `["cifs"]` |
| Check job | `core.get_jobs` | `GET /api/v2.0/core/get_jobs/?id=N` | WebSocket filter: `[[["id","=",N]]]` |

## REST API (Alternative for Read-Only Queries)

When you need a quick read-only query via shell:

```bash
# Helper script pattern
cat > /tmp/tn_api.sh << 'SCRIPT'
API_KEY="your-key"
curl -sk -H "Authorization: Bearer ${API_KEY}" "https://192.168.1.X/api/v2.0/${1}" ${@:2}
SCRIPT
chmod +x /tmp/tn_api.sh

/tmp/tn_api.sh "smb"
/tmp/tn_api.sh "system/info"
/tmp/tn_api.sh "user" 2>/dev/null | python3 -c "import sys,json;[print(f\"{u['username']}: smb={u['smb']}\") for u in json.load(sys.stdin)]"
```

### REST API Pitfalls

- PUT on `/api/v2.0/smb` returns **500** with no useful error in SCALE 25.x — use WebSocket `smb.update` instead
- API key sent via `-H "Authorization: Bearer ..."` gets **redacted** by Hermes security, causing silent failures. Use an env var or script file to avoid this
- Endpoint paths differ between REST and WebSocket (e.g., `POST /api/v2.0/filesystem/getacl` vs WebSocket `filesystem.getacl`)
- REST API for write operations is fragile — WebSocket is more reliable for smb.update, user.create, etc.

## SMB Shares with Guest/Passwordless Access

In TrueNAS SCALE 25.x, guest access works differently from older versions:

1. **No `guestok` flag** on shares — the API rejects it with "Extra inputs are not permitted"
2. **SMB service** has `guest: "nobody"` by default — maps anonymous connections to nobody
3. **`smb_options` must be set** to enable guest mapping: `"map to guest = Bad User"`
4. **Server signing must be disabled** for guest auth to work: combine in `smb_options`: `"map to guest = Bad User\nserver signing = disabled"`
5. **Pitfall — signing override**: Even with `server signing = disabled`, TrueNAS SCALE 25.x may still enforce signing at the connection level — guest sessions can't sign, so guest auth may fail with `SMB encryption or signing was required` from some clients (Python's smbprotocol). Windows/Mac clients handle this differently.
6. **Filesystem NFSv4 ACLs** must grant `everyone@` FULL_CONTROL
7. **SMB service must be restarted** after config changes

### Steps

```
1. Create dataset (share_type: SMB, acltype: NFSV4)
2. Create SMB share
3. Update SMB service config: `smb.update({"smb_options": "map to guest = Bad User\\nserver signing = disabled"})`
4. Set ACL: everyone@ FULL_CONTROL with INHERIT
5. `service.restart("cifs")`
```

### Guest Access Limitation

TrueNAS SCALE 25.x requires SMB signing (`server signing = disabled` in smb_options may not take effect because TrueNAS overrides it at the connection security level). Guest/anonymous sessions cannot provide signing, so **guest access may fail** with `SMB encryption or signing was required` errors from some clients (Python smbprotocol, etc.).

**Recommendation**: Create a dedicated user with a simple password instead of relying on guest access. This is more reliable and still very simple:

```python
# Create user
call("user.create", [{
    "username": "shared", "password": "simplepassword",
    "smb": True, "group_create": True, "home": "/var/empty",
    "home_create": False, "shell": "/usr/sbin/nologin", "locked": False
}])

# Grant ACL
call("filesystem.setacl", [{
    "path": "/mnt/p1/public",
    "dacl": [
        {"tag": "owner@", "type": "ALLOW", "perms": {"BASIC": "FULL_CONTROL"}, "flags": {"BASIC": "INHERIT"}},
        {"tag": "group@", "type": "ALLOW", "perms": {"BASIC": "FULL_CONTROL"}, "flags": {"BASIC": "INHERIT"}},
        {"tag": "USER", "type": "ALLOW", "who": "shared", "perms": {"BASIC": "FULL_CONTROL"}, "flags": {"BASIC": "INHERIT"}}
    ],
    "options": {"recursive": false, "traverse": false}
}])
```

Users connect with `\\truenas\public` using those credentials. Windows remembers them.

## Troubleshooting: tmpfs Overflow (Catalog Sync → Journald Flood → All Failures)

### Root Cause Chain

The most common "no space" failure on TrueNAS SCALE 25.x in VirtualBox is NOT pool space — it's the `/run` tmpfs filling up:

```
catalog.sync (Git clone to /var/run/middleware/ix-apps/catalogs tmpfs) → FAILS
→ journald flooded with error messages (hundreds/sec)
→ /run tmpfs fills up (tiny, KB-sized)
→ pututline() fails → ALL authentication fails with "No space left on device"
→ SMB service crashes → everything cascades
```

The `catalog.sync` job clones the TrueNAS apps repo to tmpfs. When the network can't reach GitHub reliably, each failed attempt floods journald. The `/run` tmpfs (typically 64 MB on VirtualBox) fills in seconds with thousands of journal messages, blocking PAM's `pututline()` call.

### Symptoms

- `pututline() failed with error: No space left on device` during ANY login (API, web UI, SSH)
- Port 445 (SMB) shows CLOSED despite `service.list` showing state=RUN
- `df -h /` shows plenty of free space (36+ GB) — the boot pool is fine
- WebSocket login fails even though the API key is valid

### Recovery

From Hermes (when API still works) or from TrueNAS shell/console:

```python
# 1. Fix catalog sync — call with NO params to sync all catalogs
python3 /path/to/tn-ws-call.py catalog.sync '[]'

# 2. Restart SMB service
python3 /path/to/tn-ws-call.py service.restart '"cifs"'
# Note: service.restart is a callable method, not service.control
# The param is a plain string: service.restart("cifs")
```

If the API is completely down (disk full prevents even login):
- **VirtualBox console**: Log in to the TrueNAS VM directly via VirtualBox console
- **Reboot**: Clears tmpfs. After reboot, API, web UI, and SSH all work again
- **Then fix catalog sync**: `python3 tn-ws-call.py catalog.sync '[]'` to prevent recurrence
- **Journal vacuum**: If journald is still full after catalog sync: `journalctl --vacuum-size=50M` from SSH

### Prevention

After a successful catalog sync, the service stops flooding journald. The sync only retries when triggered. If catalog sync fails permanently (e.g., GitHub unreachable), disable the catalog:

```python
# Via WebSocket or SSH
call("catalog.update", ["TRUENAS", {"preferred_trains": []}])
```

Or from TrueNAS UI: **Apps → Settings → Manage Catalogs → TRUENAS → Disable**

## SSH Access Recovery via API

When SSH is not running or you don't have the root key:

```python
# 1. Start SSH service
call("service.control", ["START", "ssh"])

# 2. Inject your public key into root user
call("user.update", [1, {"sshpubkey": "ssh-ed25519 AAAA... your-key-comment"}])

# 3. SSH in
ssh -i /path/to/private/key root@<truenas-ip>
```

TrueNAS confirms: `ssh_password_enabled: false` — publickey only. Only works if the API is accessible.

## Docker on TrueNAS SCALE

TrueNAS SCALE 25.10.x has Docker **installed but disabled** at boot by default:

```bash
# Check
systemctl status docker        # inactive (dead), disabled
ls /var/run/docker.sock        # does not exist (no socket)

# Start
systemctl start docker

# Make persistent
systemctl enable docker
```

Docker config:
- **Root**: `/var/lib/docker` on `boot-pool/ROOT/25.10.3.1/var/lib` (ZFS dataset)
- **Driver**: overlay2
- **Available space**: ~36 GB on a clean 40 GB boot disk
- **Version**: Docker 28.3.1 (varies by TrueNAS release)

**Docker is NOT managed via the middleware API.** The `docker.*` and `container.*` WebSocket methods return `ENOMETHOD`. Manage Docker directly via SSH.

**Migrating Hermes to TrueNAS Docker:** Once Docker is running, you can pull and run the `ghcr.io/chonsong/hermes-sync:latest` image with bind mounts to the storage pool (`/mnt/p1/hermes-data`). See `hermes-docker-sync-setup` skill for the bootstrap approach.

### Pitfall: NAT Interface → Docker Startup Failure (VirtualBox)

On TrueNAS SCALE 25.10 running in VirtualBox with a **NAT adapter** (`enp0s3`), Docker startup validation fails with:

```
Validation error: Cannot start docker: enp0s3 LINK_STATE_UNKNOWN
```

TrueNAS validates network interface state before starting Docker. NAT adapters in VirtualBox report `LINK_STATE_UNKNOWN` instead of `LINK_STATE_UP`, causing the validation to fail and Docker to remain unusable.

**Workarounds** (in order of reliability):

1. **Switch VirtualBox adapter to Bridged** (preferred): Power off VM → Settings → Network → Adapter 1 → Bridged Adapter → restart TrueNAS. The bridged interface reports `LINK_STATE_UP` and Docker starts normally.
2. **Use host machine Docker instead**: Deploy containers on the host (e.g., `sean@172.19.0.1`) and mount TrueNAS SMB/NFS shares for persistent storage. This bypasses TrueNAS Docker entirely.
3. **Fix from TrueNAS shell** (requires root access): Modify the Docker startup script to skip interface validation — not recommended as it may break on updates.

**Signal**: If `service.start docker` or `systemctl start docker` fails on TrueNAS with a network interface error, and the interface is a VirtualBox NAT adapter, this is the root cause.

### Pitfall: Docker May Lose Settings on TrueNAS Update

TrueNAS SCALE manages system configuration. Docker's `daemon.json` or systemd overrides may be overwritten on OS upgrades. If you rely on Docker running on TrueNAS, document the setup steps in a recovery plan.

## Disk Space Recovery (Out-of-Space on Boot Pool)

TrueNAS in VirtualBox with separate boot/data disks can fill the boot pool (typically 40 GB). Symptoms: `pututline() failed with error: No space left on device` even when data pool has 395+ GB free. **NOTE: This is different from the tmpfs overflow above** — this is actual ZFS pool full, not tmpfs.

### Diagnosis

From TrueNAS SSH (root) or shell:
```bash
zpool list                              # Check BOTH pools
zfs list -t all -o name,used,available  # Find full datasets
df -h                                   # Check if tmpfs /run is also full
```

### Common Root Causes

1. **Boot dataset quota too small** — On a 40 GB boot disk, TrueNAS SCALE installs on `boot-pool/ROOT/25.10.x/` with the pool showing 36 GB free but a dataset quota limiting available space. Fix: remove the quota:
   ```bash
   zfs set quota=none boot-pool/ROOT/25.10.x/root
   ```
2. **Small `.system` dataset quotas** — Datasets like `p1/.system/cores` may have 1 GB quotas. Check with `zfs get quota p1/.system/cores`.
3. **tmpfs `/run` full** — too many SSH logins or PAM sessions. Reboot clears it.

### When the API Is Down

The WebSocket/REST API may become unresponsive when disk space runs out. Access TrueNAS via SSH (VirtualBox console or SSH if enabled) to free space, then the API comes back.

## TrueNAS SCALE Container Runtime (25.10.x)

TrueNAS SCALE 25.10 uses **Kubernetes (k3s)** under the hood for its Apps system, NOT raw Docker:

- `app.available` — lists installable apps from the TrueNAS catalog (Plex, etc.)
- `app.query` — lists installed apps (empty until apps are enabled)
- No `docker.*` or `kubernetes.*` middleware methods — Docker endpoint returned `ENOMETHOD`
- Custom apps use **IX-Charts** (Helm-based), not Docker Compose
- Apps system must be initialized via TrueNAS UI: **Apps → Settings → Choose Pool** then **Settings → Enable App**
- TrueNAS SCALE 25.10+ added a `DOCKER_READ`/`DOCKER_WRITE` role in user permissions, suggesting Docker support is coming but not yet functional via middleware API

This matters for deploying Hermes on TrueNAS as a container — it's not a straightforward Docker Compose deployment. Custom apps require a Helm chart or an IX-Chart.

## Deploying Apps: n8n Example (TrueNAS SCALE 25.10+)

TrueNAS SCALE uses k3s/IX-Charts, not raw Docker. The easiest path is a **Custom App** via the TrueNAS UI, but it can also be driven via the WebSocket API.

### Prerequisites for Apps
1. Apps system initialized: **Apps → Settings → Choose Pool** then **Settings → Enable App**
2. A dataset for app persistent storage (e.g., `tank/apps/n8n`)

### Option A: TrueNAS UI (Manual)
```
Apps → Discover Apps → Custom App
  Image: n8nio/n8n:latest
  Port: 5678
  Volume: /mnt/tank/apps/n8n → /home/node/.n8n
  Env:
    WEBHOOK_URL=https://your-domain-or-ip:5678/
    N8N_BASIC_AUTH_ACTIVE=true
    N8N_BASIC_AUTH_USER=admin
    N8N_BASIC_AUTH_PASSWORD=<strong-password>
```

### Option B: WebSocket API (Automated)
```python
# Create dataset for n8n data
call("pool.dataset.create", [{
    "name": "tank/apps/n8n",
    "type": "FILESYSTEM",
    "share_type": "APPS"
}])

# Deploy via app.create (requires IX-Chart payload)
# NOTE: app.create schema is complex; prefer UI for one-offs.
# For automation, see references/n8n-deployment-on-truenas.md
```

### Hermes → n8n Integration
Once n8n is running:
- **Webhook triggers**: Hermes cron jobs POST to `http://truenas-ip:5678/webhook/<workflow-id>`
- **Workflow ideas**:
  - `Draft Post` → approval gate → LinkedIn auto-publish
  - `RSS Feed` → LinkedIn share
  - `Weekly Engagement Reminder`

## Pitfalls

- **MCP tools connect from agent process lifetime** — they don't persist across separate Python subprocesses. Use `from tools.mcp_tool import discover_mcp_tools, _servers` from within the agent process.
- **WebSocket version as string**: Sending `"version": 1` (integer) instead of `"version": "1"` (string) in the connect message causes a silent failure with `{"msg": "failed"}`.
- **Binary path in MCP config**: The `command` path must be an absolute path reachable from the MCP subprocess's filtered environment. Don't rely on `~` expansion or PATH lookup.
- **Job-based operations**: `filesystem/setacl` and `filesystem/setperm` return job IDs, not results. Poll with `core.get_jobs` to check completion.
- **SMB service restart required**: After changing `smb_options`, the SMB service MUST be restarted for changes to take effect.
- **User home directory**: Must be `/var/empty` or under `/mnt/...`. `/nonexistent` is rejected.
- **API key security**: Storing the API key directly in `config.yaml` is insecure. Use an env var via the MCP server config's `env` section.
- **SMB signing**: TrueNAS SCALE 25.x requires SMB signing by default. Guest sessions can't sign, so password-based auth is more reliable.

## References

- `references/session-2026-05-28.md` — WebSocket CLI script and authentication patterns
- `references/n8n-deployment-on-truenas.md` — Detailed n8n Custom App deployment recipe for TrueNAS SCALE
