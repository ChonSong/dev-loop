# Host Tunnel Architecture — 2026-06-11 (Updated)

## Critical: Three Separate Tunnels

There are **three independent Cloudflare tunnels** on the host. Each has its own credentials, config, and DNS hostname assignments. **Do NOT confuse them.**

| Domain | Tunnel ID | Tunnel Name | Credentials File | Local Config |
|--------|-----------|-------------|-----------------|--------------|
| `wiz.codeovertcp.com` | `24362d8c-acda-43ca-87d7-9f422b631b11` | gto-wizard (original) | `~/.cloudflared/gto-wizard.json` | `~/.cloudflared/gto-wizard-orig-config.yml` |
| `onetag.codeovertcp.com` | `b02e5bb6-4324-4e40-a624-e21cd128f305` | onetag-tunnel-new | `~/.hermes/cloudflared/onetag-tunnel-creds.json` | `~/.hermes/cloudflared/onetag-config.yml` |
| `skills.codeovertcp.com` | `93328a7a-43ea-4329-99d9-92d9a717dfcc` | hermes-webui | `~/.cloudflared/hermes-webui-creds.json` | `~/.hermes/cloudflared/hermes-webui-ingress.yml` |
| `hermes.codeovertcp.com` | `93328a7a` | (same as above) | (same as above) | (same as above) |

### How to Determine Which Tunnel Handles a Domain

Check the DNS record via Cloudflare API (cfut_ token has DNS read):

```python
import json, urllib.request
with open('/tmp/cf_env_clean.txt') as f:
    env = dict(line.strip().split('=', 1) for line in f if '=' in line)
req = urllib.request.Request(
    f"https://api.cloudflare.com/client/v4/zones?name=codeovertcp.com",
    headers={"Authorization": f"Bearer {env['CLOUDFLARE_USER_TOKEN']}"})
zone_id = json.loads(urllib.request.urlopen(req).read())['result'][0]['id']
req2 = urllib.request.Request(
    f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?name=wiz.codeovertcp.com",
    headers={"Authorization": f"Bearer {env['CLOUDFLARE_USER_TOKEN']}"})
print(json.dumps(json.loads(urllib.request.urlopen(req2).read())['result'], indent=2))
```

The CNAME target `XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX.cfargotunnel.com` tells you the tunnel ID.

## Server-Side Config Override (Critical)

Cloudflare's dashboard stores **server-side ingress rules**. When a tunnel connects, it pulls these configs (logged as "Updated to new configuration config=..." and a version number). **These override the local `--config` file** — local ingress rules are IGNORED when server-side rules exist.

To see what server-side config the tunnel is using, check tunnel logs:
```bash
grep "Updated to new configuration" /home/sean/.hermes/logs/cloudflared-*.log
```

### Workaround: socat Port Forwards

Since server-side config ports are fixed (dashboard), the only local-level fix is `socat` forwards on the host that bridge the dashboard-configured port to the actual container backend:

```bash
# Server says wiz → localhost:8080, but Next.js runs at 172.19.0.2:8564
nohup socat TCP-LISTEN:8080,fork,reuseaddr TCP:172.19.0.2:8564 </dev/null >/dev/null 2>&1 & disown

# Server says onetag → 127.0.0.1:8502, but Streamlit runs at 172.19.0.2:8501
nohup socat TCP-LISTEN:8502,fork,reuseaddr TCP:172.19.0.2:8501 </dev/null >/dev/null 2>&1 & disown
```

**These die on host reboot.** For persistence, either:
- Add to a systemd service on the host (`/etc/systemd/system/container-port-forwards.service` — needs sudo)
- Or create a cron-based watchdog that checks and re-creates them
- Or update the Cloudflare dashboard to point to the correct ports

## Current socat Forwards

| Host Port | Forwards To | Purpose |
|-----------|------------|---------|
| 8080 | 172.19.0.2:8564 | wiz.codeovertcp.com → Next.js (server config workaround) |
| 8564 | 172.19.0.2:8564 | GTO frontend direct access |
| 8003 | 172.19.0.2:8003 | FastAPI direct access |
| 8501 | 172.19.0.2:8501 | Streamlit direct access |
| 8502 | 172.19.0.2:8501 | onetag.codeovertcp.com → Streamlit (server config workaround) |

## DNS Records

Discovered via Cloudflare DNS API (cfut_ token):

| Domain | Type | Target | Proxied |
|--------|------|--------|---------|
| `wiz.codeovertcp.com` | CNAME | `24362d8c-....cfargotunnel.com` | Yes |
| `onetag.codeovertcp.com` | (to be checked) | (to be checked) | Yes |
| `skills.codeovertcp.com` | A | 20.11.40.34 | No |
| `hwc.codeovertcp.com` | A | Cloudflare IPs | Yes |

## Systemd Services

All tunnel services run as user `sean` with `Linger=yes` (boot persistence):

| Service | Status | Notes |
|---------|--------|-------|
| `cloudflared-hermes-webui.service` | ✅ Active | Uses `--config` or `--url` depending on setup |
| `cloudflared-onetag.service` | ✅ Active | Config-based |
| `cloudflared-hwc.service` | ✅ Active | Quick tunnel (no custom domain) |

## Useful Commands

```bash
# Check tunnel processes on host
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 "pgrep -a cloudflared | grep -v agent-os"

# Check tunnel logs
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 \
  "tail -20 /home/sean/.hermes/logs/cloudflared-hermes-webui.log"

# Restart a tunnel
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 \
  "systemctl --user restart cloudflared-hermes-webui"

# Start a tunnel without systemd (bare)
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 \
  'nohup /home/sean/.hermes/bin/cloudflared --no-autoupdate tunnel --config /path/to/config.yml run > /dev/null 2>&1 & disown'

# Start socat forward (survives SSH)
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 \
  'nohup socat TCP-LISTEN:8080,fork,reuseaddr TCP:172.19.0.2:8564 </dev/null >/dev/null 2>&1 & disown'
```

## Pitfalls

- `pkill -f cloudflared` can kill the SSH session itself (pattern match on `cloudflared` in the SSH command). Be specific with PID numbers or use `systemctl --user stop`.
- Tunnel credentials files look like JSON with `AccountTag`, `TunnelID`, `TunnelName`, `TunnelSecret`. The `TunnelID` must match the ID in DNS's CNAME target.
- The `cfat_` API token is read-only for tunnel config. Use the Cloudflare dashboard or a write-capable token to modify server-side ingress rules.
- The `cfut_` token (Zone:DNS:Edit permission) can read/write DNS records but NOT tunnel configs.
- Multiple tunnel configs with the same name but different IDs exist: `hermes-webui` has BOTH `bf723d4c` and `93328a7a`. The `93328a7a` is the one currently used by systemd services.
