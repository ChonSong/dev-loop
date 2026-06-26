# Cloudflare Access App — Configuration Reference

## Access App and Identity Provider Linkage

A critical step when creating an Access App via API: **the `allowed_idps` field must be explicitly set** to link the Access App to an Identity Provider. Without this, the Access App returns `allowed_idps: []` and users see "Access denied" with no login prompt.

**Pre-existing IdP on the account:**
- Email OTP (One-Time PIN): `49f403a4-1319-4d39-9a93-c4a430cf19d3`
  - Type: `onetimepin`
  - Created automatically when Zero Trust email OTP is enabled in the dashboard

**Link IdP to Access App via PUT** (not PATCH):
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

**Why PATCH fails:** PATCH on `/access/apps/{id}` returns "Method not allowed for this authentication scheme" when trying to set `allowed_idps`. PUT works correctly.

**Why PATCH fails (identity_providers):** The endpoint `/access/identity_providers` (capital P) returns 404. The IdP is managed in the Zero Trust dashboard, not via the Access apps endpoint — you just reference its UUID in `allowed_idps`.

## Tunnel Secret Mismatch — Fix via API

**Symptom:** cloudflared repeatedly exits with:
```
ERR Register tunnel error from server side error="Unauthorized: Invalid tunnel secret"
```

**Root cause:** The `tunnel_secret` in the credentials file (`~/.cloudflared/hermes-webui-creds.json`) does not match what Cloudflare has stored for the tunnel.

**Fix — reset tunnel secret via API PATCH:**
```bash
curl -s -X PATCH "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/cfd_tunnel/$TUNNEL_ID" \
  -H "X-Auth-Key: $GLOBAL_API_KEY" \
  -H "X-Auth-Email: $CF_EMAIL" \
  -H "Content-Type: application/json" \
  -d "{\"tunnel_secret\": \"$TUNNEL_SECRET_B64\"}"
```

The credentials file has the canonical secret — use the `tunnel_secret` value from it. Cloudflare accepts base64-encoded secret in the PATCH body.

**After patching:** restart the cloudflared process. Tunnel should register immediately with `Status: healthy | Connections: N`.

## Access App Verification

Check Access is enforcing auth:
```bash
curl -sI https://hermes.codeovertcp.com
# Returns HTTP/2 302 with Location: https://<account>.cloudflareaccess.com/cdn-cgi/access/login/<domain>?kid=...
# Also shows: www-authenticate: Cloudflare-Access
```

Verify IdP linkage on the Access App:
```bash
curl -s "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/access/apps/$APP_ID" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" | python3 -c "
import json,sys
app = json.load(sys.stdin)['result']
print('allowed_idps:', app.get('allowed_idps'))
print('domain:', app.get('domain'))
print('type:', app.get('type'))
"
```

## Final Working Config

| Item | Value |
|------|-------|
| Tunnel ID | `bf723d4c-7299-4a6b-a2f9-6cee6bec86dc` |
| Tunnel credentials | `/opt/data/cloudflared/hermes-webui-creds.json` |
| Tunnel secret | `fYgNBpa4fD5/r2YzwNN1ku7BbHLaTzbV9r4L5vtL53PuX/EbIcRASY5a9E8tJvlpyISr/8Lm+v+zFVn/0DPxjQ==` |
| Access App ID | `e39862fe-f5c9-421d-93a8-3c6657ecddac` |
| Access Policy ID | `4802fe7d-5868-4987-8c48-263984697a6d` |
| Email OTP IdP | `49f403a4-1319-4d39-9a93-c4a430cf19d3` |
| DNS Record ID | `13fb48dbc8771a2dd1beaac9306e03a9` |
| Zone | `a0dc1c2d5a810fabb43cb596a7e4b322` |
| Account | `fd4058c7aa1da2cb3ec2f2c9f028c022` |

**Working tunnel run command (cloudflared v2026.5.0):**
```bash
/tmp/cloudflared --no-autoupdate \
  --credentials-file /opt/data/cloudflared/hermes-webui-creds.json \
  tunnel run --url http://172.19.0.2:8787 hermes-webui
```

> Note: `tunnel run <name>` must be the **last positional argument** on v2026.5.0. Flags after it are not accepted.

## Watchdog Script (Alternative to systemd)

When DBUS session bus is unavailable (agent environment, no `systemctl --user`), use a watchdog script instead:
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
  sleep 1
  nohup $BIN --no-autoupdate --credentials-file $CRED tunnel run --url $TARGET $TUNNEL_NAME >> "$LOG" 2>&1 &
  log "Tunnel restarted with PID $!"
}

if pgrep -f "cloudflared.*$TUNNEL_NAME" > /dev/null; then
  log "Tunnel is running"
else
  log "Tunnel not running"
  restart_tunnel
fi
```

Run via cron: `*/5 * * * * /opt/data/scripts/hermes-webui-tunnel-watchdog.sh`