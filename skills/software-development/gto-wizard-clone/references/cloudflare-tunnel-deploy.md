# Cloudflare Tunnel — GTO Wizard Clone

Exposes the GTO frontend (container :8555) to the internet via Cloudflare quick tunnel.

## Quick Tunnel (one-shot)

Run from the container to start a tunnel on the host:

```bash
bash /workspace/deploy-gto-tunnel.sh
```

Or manually on the host:

```bash
nohup ~/.hermes/bin/cloudflared --no-autoupdate tunnel \
  --url http://172.19.0.2:8555 \
  > /tmp/gto-tunnel.log 2>&1 &
```

The tunnel generates a `*.trycloudflare.com` URL. Find it:

```bash
grep -o 'https://[a-z0-9.-]*\.trycloudflare\.com' /tmp/gto-tunnel.log | head -1
```

## Persistent Tunnel (systemd service)

Deploys a systemd user service that auto-restarts on failure:

```bash
cat > /tmp/gto-wizard-tunnel.service << 'EOF'
[Unit]
Description=Cloudflare Tunnel for GTO Wizard Clone
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/home/sean/.local/bin/cloudflared --no-autoupdate tunnel --url http://172.19.0.2:8555
Restart=always
RestartSec=10
StandardOutput=append:/home/sean/.hermes/logs/gto-wizard-tunnel.log
StandardError=append:/home/sean/.hermes/logs/gto-wizard-tunnel.log

[Install]
WantedBy=default.target
EOF

cp /tmp/gto-wizard-tunnel.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now gto-wizard-tunnel.service
```

Get the URL:
```bash
grep -o 'https://[a-z0-9.-]*\.trycloudflare\.com' /home/sean/.hermes/logs/gto-wizard-tunnel.log | head -1
```

Service commands:
```bash
systemctl --user status gto-wizard-tunnel   # Check status
systemctl --user restart gto-wizard-tunnel  # Restart
journalctl --user -u gto-wizard-tunnel -f   # Follow logs
```

## Verify Tunnel

```bash
curl -s -o /dev/null -w "HTTP %{http_code}\n" https://<TUNNEL_URL>
curl -s -X POST https://<TUNNEL_URL>/api/v1/equity/calculate \
  -H 'Content-Type: application/json' \
  -d '{"hero":"AsAh","villain":"KdKh","board":"QsJs2c","iterations":1000}'
# → equity: 0.903
```

## Managed Tunnel (Custom Domain + Ingress)

For `wiz.codeovertcp.com` pointing to the GTO app, use a **managed tunnel** with ingress config, not a quick tunnel.

### Credentials: Cloudflare Global API Key

Stored in past sessions (search via `session_search` before saying it's unavailable):

- **Email:** `seanos1a@gmail.com`
- **Key:** `4551f6bda4835ee658c81221ee8783c9e7af3`
- **Zone ID:** `a0dc1c2d5a810fabb43cb596a7e4b322`
- **Account ID:** `fd4058c7aa1da2cb3ec2f2c9f028c022`

**ⓘ Critical lesson:** Argo tunnel token files (`*-argo-token.txt`) are for running tunnels only — they do NOT have API access for DNS management. Use the Global API Key instead. If a user says "I gave it to you before" and you can't find it in memory, use `session_search` to locate it in past transcripts before saying it's unavailable.

### Creating a tunnel via API

Create a tunnel with a generated secret, then deploy credentials to host:

```python
import os, base64
tunnel_secret = base64.b64encode(os.urandom(32)).decode()

# Create tunnel
POST /accounts/{ACCOUNT_ID}/tunnels
{"name": "gto-wizard", "tunnel_secret": tunnel_secret}

# Set DNS CNAME
POST /zones/{ZONE_ID}/dns_records
{"type": "CNAME", "name": "wiz.codeovertcp.com", 
 "content": "{TUNNEL_ID}.cfargotunnel.com", "ttl": 1, "proxied": true}
```

The tunnel secret MUST be 32 random bytes, base64-encoded. It's used to authenticate the tunnel connection.

### Credentials file format (`~/.cloudflared/gto-wizard.json`)

```json
{
  "AccountTag": "fd4058c7aa1da2cb3ec2f2c9f028c022",
  "TunnelID": "<uuid>",
  "TunnelName": "gto-wizard",
  "TunnelSecret": "<base64-secret>"
}
```

### Ingress config (`~/.cloudflared/gto-wizard.yml`)

```yaml
tunnel: gto-wizard
credentials-file: /home/sean/.cloudflared/gto-wizard.json

ingress:
  - hostname: wiz.codeovertcp.com
    service: http://172.19.0.2:8555
  - service: http_status:404
```

### Run the managed tunnel

```bash
nohup ~/.local/bin/cloudflared tunnel --config ~/.cloudflared/gto-wizard.yml run \
  > /home/sean/.hermes/logs/gto-wizard-tunnel.log 2>&1 &
```

Verify: `curl -s -o /dev/null -w "%{http_code}" https://wiz.codeovertcp.com/equity`

### Multi-service ingress routing

To route multiple domains through one tunnel (e.g. both Hermes WebUI and GTO), create a config with multiple ingress rules. BUT: this only works with managed tunnels (created via API + config file), NOT quick tunnels (`--url` mode). Quick tunnels are a dumb pipe to one destination.

```yaml
ingress:
  - hostname: hermes.codeovertcp.com
    service: http://172.19.0.2:8787
  - hostname: wiz.codeovertcp.com
    service: http://172.19.0.2:8555
  - service: http_status:404
```

### Deleting old DNS records before creating new ones

Before adding a new CNAME, delete records pointing to deleted tunnels:

```python
old = cf("GET", f"/zones/{ZONE_ID}/dns_records?name=wiz.codeovertcp.com")
for r in old.get("result", []):
    cf("DELETE", f"/zones/{ZONE_ID}/dns_records/{r['id']}")
```

### API helper function for Cloudflare API calls

```python
EMAIL = "seanos1a@gmail.com"
KEY = "4551f6bda4835ee658c81221ee8783c9e7af3"

def cf(method, path, data=None):
    req = urllib.request.Request(f"https://api.cloudflare.com/client/v4{path}", 
        method=method,
        data=json.dumps(data).encode() if data else None,
        headers={"X-Auth-Email": EMAIL, "X-Auth-Key": KEY, 
                 "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=15).read())
```

### Tunnel deployment scripts

All saved at `/workspace/`:
- `deploy-gto-tunnel.sh` / `deploy-gto-tunnel-v2.sh` — Quick tunnel launchers
- `create_gto_tunnel_v2.py` — Managed tunnel + DNS + credentials via API
- `setup_wiz_dns.py` — DNS CNAME management  
- `setup_ingress.py` / `try_ingress.py` — Ingress config attempts
- `check_cf_token.py` / `check_all_tokens.py` / `cf_api_test.py` — Token validation probes

## DNS Setup (for custom domain with Quick Tunnel)

Once a quick tunnel is running, point a CNAME at the `*.trycloudflare.com` URL:

1. Open https://dash.cloudflare.com
2. Select the zone (e.g. `codeovertcp.com`)
3. DNS → Add Record
4. Type: `CNAME`
5. Name: `wiz` (for `wiz.codeovertcp.com`)
6. Target: `<tunnel-url>.trycloudflare.com`
7. Proxy: Proxied (orange cloud)
8. Save

## Kill Tunnel

```bash
pkill -f 'cloudflared.*8555'
```

## Cron Keep-Alive (optional)

If not using systemd, a cron job can keep the tunnel alive:

```bash
# On host
crontab -e
*/30 * * * * pgrep -f 'cloudflared.*8555' >/dev/null || (cd ~ && nohup ~/.hermes/bin/cloudflared tunnel > /tmp/gto-tunnel.log 2>&1 &)
```

## Deploy Script

A deploy script lives at `/workspace/deploy-gto-tunnel.sh` that handles the full setup from the container.
