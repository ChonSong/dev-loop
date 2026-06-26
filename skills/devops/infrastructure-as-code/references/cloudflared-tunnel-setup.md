# Cloudflare Tunnel — Setup & Debug Reference

## hermes-webui tunnel end-to-end config

| Item | Value |
|------|-------|
| Tunnel ID | `bf723d4c-7299-4a6b-a2f9-6cee6bec86dc` |
| Tunnel credentials | `/opt/data/cloudflared/hermes-webui-creds.json` |
| Tunnel secret (base64) | `fYgNBpa4fD5/r2YzwNN1ku7BbHLaTzbV9r4L5vtL53PuX/EbIcRASY5a9E8tJvlpyISr/8Lm+v+zFVn/0DPxjQ==` |
| Access App ID | `e39862fe-f5c9-421d-93a8-3c6657ecddac` |
| Access Policy ID | `4802fe7d-5868-4987-8c48-263984697a6d` |
| Email OTP IdP | `49f403a4-1319-4d39-9a93-c4a430cf19d3` |
| DNS Record ID | `13fb48dbc8771a2dd1beaac9306e03a9` |
| Zone | `a0dc1c2d5a810fabb43cb596a7e4b322` |
| Account | `fd4058c7aa1da2cb3ec2f2c9f028c022` |

## Working tunnel run command (cloudflared v2026.5.0)

```bash
/tmp/cloudflared tunnel run \
  --credentials-file /opt/data/cloudflared/hermes-webui-creds.json \
  --url http://172.19.0.2:8787 hermes-webui \
  >> /tmp/hermes-tunnel.log 2>&1 &
```

> **Critical:** `tunnel run <name>` must be the **last positional argument** on v2026.5.0. Flags after it are silently ignored.

## Network path

```
Cloudflare Edge (HTTPS + Access)
  → cloudflared host process (PID X)
  → Docker bridge: 172.19.0.2:8787 (hermes-webui container)
```

- hermes-webui container: `hermes-webui-hermes-webui-1`, IP `172.19.0.2`, published at `127.0.0.1:8787`
- cloudflared runs on host (not in Docker) to reach the Docker bridge IP
- cloudflared is at `/tmp/cloudflared` (v2026.5.0) — **NOT** in a container

## Multiple cloudflared processes = 502 even with healthy tunnel

**This is the #1 cause of 502 after successful Access login.**

Running more than one cloudflared process with the same tunnel credentials causes a "control stream encountered a failure while serving" cascade. Cloudflare shows "healthy | Connections: 8" but actual browser traffic gets 502.

**Symptoms:**
- `curl -sI https://hermes.codeovertcp.com` → `HTTP/2 302` + Access redirect (looks fine)
- Browser completes Access email OTP login successfully
- After login: **502 Bad Gateway** from Cloudflare edge
- Tunnel log: `ERR failed to serve tunnel connection` / `control stream encountered a failure` / `context canceled`
- Cloudflare dashboard: tunnel "healthy | Connections: 8" — misleading

**Diagnosis sequence:**
```bash
# Step 1: Find ALL cloudflared processes (including zombies)
pgrep -la cloudflared

# Step 2: Kill them all — zombies need -9 on each PID individually
pkill -f cloudflared; sleep 2
pgrep -la cloudflared
# If <defunct> zombies remain:
kill -9 <pid1> <pid2> ...

# Step 3: Verify clean
pgrep -la cloudflared || echo "CLEAN"

# Step 4: Start ONE fresh tunnel with logging
> /tmp/hermes-tunnel.log  # truncate old log
/tmp/cloudflared tunnel run \
  --credentials-file /opt/data/cloudflared/hermes-webui-creds.json \
  --url http://172.19.0.2:8787 hermes-webui \
  >> /tmp/hermes-tunnel.log 2>&1 &

# Step 5: Verify log shows healthy connections
sleep 10 && tail /tmp/hermes-tunnel.log
# Should see: "Registered tunnel connection connIndex=N ... location=..."

# Step 6: Confirm no control-stream errors
grep -i "error\|fail" /tmp/hermes-tunnel.log
# Should be empty (warnings are OK, errors are not)
```

**Why zombies need `kill -9 <pid>`:** defunct processes are already dead — `pkill -9` by name doesn't reach them. Must use `kill -9 <pid>` on each zombie PID individually.

**Rule: one process per tunnel credential file, always.** Kill old before starting new.

## Access App + IdP linkage

**Pre-existing IdP on the account:**
- Email OTP (One-Time PIN): `49f403a4-1319-4d39-9a93-c4a430cf19d3`

**Link IdP to Access App via PUT** (PATCH fails with "Method not allowed for this authentication scheme"):
```bash
curl -s -X PUT "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/access/apps/$APP_ID" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "$APP_ID",
    "name": "hermes-webui",
    "domain": "hermes.codeovertcp.com",
    "type": "self_hosted",
    "session_duration": "24h",
    "allowed_idps": ["49f403a4-1319-4d39-9a93-c4a430cf19d3"]
  }'
```

## Tunnel secret mismatch — fix via API

**Symptom:**
```
ERR Register tunnel error from server side error="Unauthorized: Invalid tunnel secret"
```

**Fix — reset tunnel secret via API PATCH** (use `tunnel_secret` value from credentials file):
```bash
curl -s -X PATCH "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/cfd_tunnel/$TUNNEL_ID" \
  -H "X-Auth-Key: $GLOBAL_API_KEY" \
  -H "X-Auth-Email: seanos1a@gmail.com" \
  -H "Content-Type: application/json" \
  -d "{\"tunnel_secret\": \"$TUNNEL_SECRET_B64\"}"
```

## Access verification

```bash
# Check Access is enforcing (should 302 to cloudflareaccess.com)
curl -sI https://hermes.codeovertcp.com
# Must show: www-authenticate: Cloudflare-Access

# Verify IdP linkage
curl -s "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/access/apps/$APP_ID" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" | \
  python3 -c "import json,sys; app=json.load(sys.stdin)['result']; print('allowed_idps:', app.get('allowed_idps'))"
```

## Watchdog script (no systemd / no DBUS)

When `systemctl --user` fails (no DBUS session bus), run via cron:
```bash
*/5 * * * * /opt/data/scripts/hermes-webui-tunnel-watchdog.sh
```

```bash
#!/bin/bash
# /opt/data/scripts/hermes-webui-tunnel-watchdog.sh
LOG=/opt/data/logs/hermes-webui-tunnel.log
CRED=/opt/data/cloudflared/hermes-webui-creds.json
TUNNEL_NAME=hermes-webui
TARGET=http://172.19.0.2:8787
BIN=/tmp/cloudflared

log() { echo "[$(date)] $*" >> "$LOG"; }

restart_tunnel() {
  log "Restarting cloudflared tunnel..."
  pkill -f "cloudflared.*$TUNNEL_NAME" 2>/dev/null
  sleep 2
  nohup $BIN --credentials-file $CRED tunnel run --url $TARGET $TUNNEL_NAME >> "$LOG" 2>&1 &
  log "Tunnel restarted with PID $!"
}

if pgrep -f "cloudflared.*$TUNNEL_NAME" > /dev/null; then
  log "Tunnel is running"
else
  log "Tunnel not running"
  restart_tunnel
fi
```

## Token types and API scope

| Token | Prefix | API access | tunnel management |
|-------|--------|-----------|-------------------|
| Cloudflare Access API token | `cfat_` | Access API only (`/access/...`) | ❌ code 9109 |
| Cloudflare API token | `cfut_` or bare | Full API | ✅ |
| Global API Key | (raw key) | Full API (via X-Auth-Key header) | ✅ |

When `cfat_` returns 9109 on tunnel API calls, fall back to Global API Key + `X-Auth-Key`/`X-Auth-Email` headers.