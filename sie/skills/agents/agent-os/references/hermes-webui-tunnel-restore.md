# hermes.codeovertcp.com Tunnel Restore (2026-05-20)

## What Happened

hermes.codeovertcp.com went down. Restored by running the cloudflared tunnel directly on the host/container as a background process with a watchdog.

## Architecture

```
hermes.codeovertcp.com (Cloudflare Access)
    ↓ HTTPS (CNAME → bf723d4c.cfargotunnel.com)
hermes-webui tunnel (Cloudflare Named Tunnel)
    ↓
http://hermes-webui-hermes-webui-1:8787 (Docker internal DNS)
    ↓
hermes-webui container (Go+Svelte5 web UI, port 8787)
```

- **Tunnel ID**: `bf723d4c-7299-4a6b-a2f9-6cee6bec86dc`
- **Tunnel Name**: `hermes-webui`
- **Tunnel credential secret** (base64): `fYgNBpa4fD5/r2YzwNN1ku7BbHLaTzbV9r4L5vtL53PuX/EbIcRASY5a9E8tJvlpyISr/8Lm+v+zFVn/0DPxjQ==`
- **Account ID**: `fd4058c7aa1da2cb3ec2f2c9f028c022`
- **Target hostname**: `hermes.codeovertcp.com` (CNAME → `<tunnel_id>.cfargotunnel.com`, proxied)
- **Target service**: `http://hermes-webui-hermes-webui-1:8787`

## Persistent Files

| File | Purpose |
|------|---------|
| `/opt/data/bin/cloudflared` | cloudflared binary v2026.5.0 (host-level install) |
| `/opt/data/cloudflared/hermes-webui-creds.json` | Tunnel credentials (JSON, not JWT) |
| `/opt/data/cloudflared/hermes-webui.yml` | Ingress config |
| `/opt/data/scripts/hermes-webui-tunnel-watchdog.sh` | Watchdog script (checks every 30s) |
| `/opt/data/home/.hermes/scripts/hermes-webui-tunnel-watchdog.sh` | Cron-accessible copy |
| `/opt/data/logs/cloudflared-watchdog.log` | Watchdog restart log |

## Run Command

```bash
/opt/data/bin/cloudflared tunnel run \
  --credentials-file /opt/data/cloudflared/hermes-webui-creds.json \
  hermes-webui
```

No `--url` flag needed — ingress rules in `hermes-webui.yml` handle routing by hostname.

## Ingress Config (`hermes-webui.yml`)

```yaml
tunnel: bf723d4c-7299-4a6b-a2f9-6cee6bec86dc
credentials-file: /etc/cloudflared/hermes-webui-creds.json

ingress:
  - hostname: hermes.codeovertcp.com
    service: http://hermes-webui-hermes-webui-1:8787
  - service: http_status:404
```

## Watchdog Script

```bash
#!/bin/bash
CREDS="/opt/data/cloudflared/hermes-webui-creds.json"
BINARY="/opt/data/bin/cloudflared"
WEBUI_IP="172.19.0.2"
WEBUI_PORT="8787"
LOG="/opt/data/logs/cloudflared-watchdog.log"

if ! pgrep -f "$BINARY.*hermes-webui" > /dev/null 2>&1; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Tunnel dead, restarting..." >> $LOG
    $BINARY tunnel run --credentials-file $CREDS --url http://${WEBUI_IP}:${WEBUI_PORT} hermes-webui 2>&1 &
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Started PID=$!" >> $LOG
fi
```

## Cron Guardian

```bash
hermes cron add hermes-webui-tunnel-guardian \
  --script hermes-webui-tunnel-watchdog.sh \
  --schedule "*/5 * * * *" \
  --no-agent \
  --prompt "Run /opt/data/home/.hermes/scripts/hermes-webui-tunnel-watchdog.sh..."
```

Runs every 5 minutes. Script checks if cloudflared process is alive; restarts if dead.

## Discovery Process

1. **List all tunnels** via Cloudflare API:
   ```bash
   curl -s -X GET "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/tunnels" \
     -H "Authorization: Bearer ${CFAT_TOKEN}" | python3 -c "
   import json,sys
   d=json.load(sys.stdin)
   for t in d.get('result', []):
       print(t['id'], t['name'], t.get('status'), len(t.get('connections',[])))
   "
   ```

2. **Get tunnel credentials** (camelCase JSON):
   ```bash
   curl -s -X GET "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/tunnels/${TUNNEL_ID}/credentials" \
     -H "Authorization: Bearer ${CFAT_TOKEN}" | python3 -m json.tool
   ```
   Returns: `AccountTag`, `TunnelID`, `TunnelSecret` (base64).

3. **Extract token file from running container** (if exists):
   ```bash
   docker cp <container>:/etc/cloudflared/<token-file>.txt /tmp/argo-token.txt
   ```

4. **Reconstruct credentials file** from known tunnel ID + account ID + secret.

## Key Lessons

1. **cloudflared entrypoint**: The `cloudflare/cloudflared:*` image has entrypoint `["cloudflared", "--no-autoupdate"]` and CMD `["version"]`. To run tunnel commands, pass full args: `cloudflared --no-autoupdate tunnel run ...`.

2. **No `sh` in minimal containers**: Many cloudflared-based containers ship without `sh` or `cat`. Use `cloudflared tunnel info`, `cloudflared tunnel list` as exec commands.

3. **Watchdog vs systemd**: Inside the hermes container (no systemd), watchdog script + cron is the persistence pattern. On a host with systemd, use a proper service unit.

4. **Token vs credentials**: The `--token-file` takes a JWT (240 bytes, starts with `eyJ`). The `--credentials-file` takes a JSON file with `TunnelSecret`. Don't mix them up.

5. **Named tunnel ingress routing**: With a credentials-file (named tunnel), ingress rules in the config file route by hostname. No `--url` flag needed when ingress rules are set.

6. **Extract credentials from Cloudflare API**: If credentials file is lost but tunnel ID and account ID are known, reconstruct from API: `GET /accounts/{id}/tunnels/{id}/credentials`.

## Debug Commands

```bash
# Check if tunnel process is running
ps aux | grep "[c]loudflared.*hermes-webui"

# Test public endpoint
curl -sL --max-time 8 https://hermes.codeovertcp.com | grep title

# Check tunnel connections via Cloudflare API
curl -s "https://api.cloudflare.com/client/v4/accounts/fd4058c7aa1da2cb3ec2f2c9f028c022/tunnels/bf723d4c-7299-4a6b-a2f9-6cee6bec86dc" \
  -H "Authorization: Bearer ${CFAT_TOKEN}" | python3 -m json.tool

# Check watchdog log
tail -20 /opt/data/logs/cloudflared-watchdog.log

# Manually restart tunnel
kill $(pgrep -f "cloudflared.*hermes-webui") && \
  /opt/data/bin/cloudflared tunnel run --credentials-file /opt/data/cloudflared/hermes-webui-creds.json hermes-webui 2>&1 &
```

## Related

- `references/cloudflare-tunnel-debug.md` — token types, DNS, credentials format, trycloudflare gotchas
- `references/cloudflared-tunnel-fix.md` — old hostname fix (backend:3001 vs agent-os-backend)
