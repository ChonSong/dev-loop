# hermes.codeovertcp.com Tunnel Restore (2026-05-20)

## What Happened

hermes.codeovertcp.com went down. Restored by running cloudflared tunnel directly on the host/container as a background process with a watchdog.

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
- **Account ID**: `fd4058c7aa1da2cb3ec2f2c9f028c022`
- **Target hostname**: `hermes.codeovertcp.com` (CNAME → `<tunnel_id>.cfargotunnel.com`, proxied)
- **Target service**: `http://hermes-webui-hermes-webui-1:8787`

## Persistent Files

| File | Purpose |
|------|---------|
| `/opt/data/bin/cloudflared` | cloudflared binary v2026.5.0 |
| `/opt/data/cloudflared/hermes-webui-creds.json` | Tunnel credentials |
| `/opt/data/cloudflared/hermes-webui.yml` | Ingress config |
| `/opt/data/scripts/hermes-webui-tunnel-watchdog.sh` | Watchdog (checks every 30s) |
| `/opt/data/home/.hermes/scripts/hermes-webui-tunnel-watchdog.sh` | Cron-accessible copy |
| `/opt/data/logs/cloudflared-watchdog.log` | Restart log |

## Run Command

```bash
/opt/data/bin/cloudflared tunnel run \
  --credentials-file /opt/data/cloudflared/hermes-webui-creds.json \
  hermes-webui
```

No `--url` flag needed — ingress rules in the yml handle routing by hostname.

## Cron Guardian

```bash
hermes cron add hermes-webui-tunnel-guardian \
  --script hermes-webui-tunnel-watchdog.sh \
  --schedule "*/5 * * * *" \
  --no-agent \
  --prompt "Run /opt/data/home/.hermes/scripts/hermes-webui-tunnel-watchdog.sh..."
```

## Key Lessons

1. **cloudflared entrypoint**: The `cloudflare/cloudflared:*` image has entrypoint `["cloudflared", "--no-autoupdate"]` and CMD `["version"]`. Pass full args: `cloudflared --no-autoupdate tunnel run ...`.

2. **No `sh` in minimal containers**: cloudflared-based containers often ship without `sh` or `cat`. Use `cloudflared tunnel info`, `cloudflared tunnel list` as exec commands.

3. **Watchdog vs systemd**: Inside the hermes container (no systemd), watchdog script + cron is the persistence pattern. On a host with systemd, use a proper service unit.

4. **Token vs credentials**: `--token-file` takes a JWT (240 bytes, starts with `eyJ`). `--credentials-file` takes a JSON file with `TunnelSecret`. Don't mix them up.

5. **Named tunnel ingress routing**: With credentials-file (named tunnel), ingress rules in the config file route by hostname. No `--url` flag needed when ingress rules are set.

6. **Reconstruct credentials from Cloudflare API**: If credentials file is lost but tunnel ID and account ID are known:
   ```bash
   curl -s -X GET "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/tunnels/${TUNNEL_ID}/credentials" \
     -H "Authorization: Bearer ${CFAT_TOKEN}" | python3 -m json.tool
   ```

## Debug Commands

```bash
# Check if tunnel process is running
ps aux | grep "[c]loudflared.*hermes-webui"

# Test public endpoint
curl -sL --max-time 8 https://hermes.codeovertcp.com | grep title

# Manually restart tunnel
kill $(pgrep -f "cloudflared.*hermes-webui") && \
  /opt/data/bin/cloudflared tunnel run \
    --credentials-file /opt/data/cloudflared/hermes-webui-creds.json \
    hermes-webui 2>&1 &
```

## Related

- `agent-os` skill `references/hermes-webui-tunnel-restore.md` — same content, canonical version
