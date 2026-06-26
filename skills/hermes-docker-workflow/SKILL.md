---
name: hermes-docker-workflow
description: "Build, run, and troubleshoot Hermes Agent Docker containers. For Ubuntu/hpprobook host (NOT Arch). Covers docker-compose, exec, GHCR image push/pull, Cloudflare tunnels, and known path/binary quirks."
---

# Hermes Docker Workflow

## Cloudflare Tunnel — Complete Operational Guide

### Binary Placement (CRITICAL)
- **NEVER** place cloudflared binary in `/tmp` — it's tmpfs and gets wiped on reboot
- **ALWAYS** use persistent path: `/home/sean/.hermes/bin/cloudflared`
- **ALWAYS** use `--no-autoupdate` flag — auto-update replaces the binary in-place, killing the running process

### Tunnel Persistence via systemd User Services

```bash
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/cloudflared-<name>.service << EOF
[Unit]
Description=Cloudflare Tunnel for <name>
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/home/sean/.hermes/bin/cloudflared --no-autoupdate tunnel run --credentials-file /home/sean/.cloudflared/<name>-creds.json --url http://<origin> <tunnel-name>
Restart=always
RestartSec=5
StandardOutput=append:/home/sean/.hermes/logs/cloudflared-<name>.log
StandardError=append:/home/sean/.hermes/logs/cloudflared-<name>.log

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable cloudflared-<name>
systemctl --user start cloudflared-<name>
```

**Pitfall**: If disk is 100% full, `systemctl --user enable` silently creates a 0-byte masked service file. Always check `df -h` first.

### Recreating a Tunnel — Full Procedure

```bash
# 1. Delete old tunnel
curl -s -X DELETE "https://api.cloudflare.com/client/v4/accounts/<ACCOUNT_ID>/tunnels/<OLD_ID>" \
  -H "X-Auth-Email: <EMAIL>" -H "X-Auth-Key: <GLOBAL_KEY>"

# 2. Create new tunnel (credentials embedded in response)
curl -s -X POST "https://api.cloudflare.com/client/v4/accounts/<ACCOUNT_ID>/tunnels" \
  -H "X-Auth-Email: <EMAIL>" -H "X-Auth-Key: <GLOBAL_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"name":"<tunnel-name>"}' > /tmp/tunnel.json

# 3. Extract credentials (camelCase → JSON)
python3 -c "
import json
d = json.load(open('/tmp/tunnel.json'))
r = d['result']
cf = r['credentials_file']
creds = {'AccountTag': cf['AccountTag'], 'TunnelID': cf['TunnelID'], 'TunnelName': cf['TunnelName'], 'TunnelSecret': cf['TunnelSecret']}
with open('/tmp/creds.json','w') as f: json.dump(creds, f, indent=2)
print('TunnelID:', cf['TunnelID'])
"

# 4. Upload creds to host persistent path
# 5. Update DNS CNAME → <NEW_TUNNEL_ID>.cfargotunnel.com (proxied)
# 6. Set ingress rules:
curl -s -X PUT "https://api.cloudflare.com/client/v4/accounts/<ACCOUNT_ID>/cfd_tunnel/<NEW_TUNNEL_ID>/configurations" \
  -H "X-Auth-Email: <EMAIL>" -H "X-Auth-Key: <GLOBAL_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"config":{"ingress":[{"hostname":"<hostname>","service":"http://<origin>"},{"service":"http_status:404"}]}}'
# 7. Restart: systemctl --user restart cloudflared-<name>
```

### Ingress Rules — Common Pitfall
**Symptom**: Tunnel healthy, DNS resolves, browser gets 404 after CF Access auth.
**Cause**: Ingress config missing the hostname — falls through to `http_status:404`.
**Fix**: Add hostname via `cfd_tunnel/<id>/configurations` PUT.

### Cloudflare Access App Creation
```bash
curl -s -X POST "https://api.cloudflare.com/client/v4/accounts/<ACCOUNT_ID>/access/apps" \
  -H "X-Auth-Email: <EMAIL>" -H "X-Auth-Key: <GLOBAL_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"name":"<app>","domain":"<hostname>","type":"self_hosted","session_duration":"24h","allowed_idps":["<IDP_ID>"],"policies":[{"name":"allow","decision":"allow","include":[{"email":{"email":"<email>"}}]}]}'
```

### API Auth
| Type | Header | Scope |
|---|---|---|
| Global API Key | `X-Auth-Email` + `X-Auth-Key` | Everything |
| API Token | `Authorization: Bearer` | Token-scoped only |
| CF Access Token | `Authorization: Bearer` | Access policies only |

**Account ID**: `fd4058c7aa1da2cb3ec2f2c9f028c022` · **Zone ID**: `a0dc1c2d5a810fabb43cb596a7e4b322`

### Watchdog Pattern (no systemd)
```bash
#!/bin/bash
CRED="/home/sean/.cloudflared/<name>-creds.json"
BIN="/home/sean/.hermes/bin/cloudflared"
LOG="/home/sean/.hermes/logs/<name>.log"
[ ! -f "$BIN" ] && curl -sL "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64" -o "$BIN" && chmod +x "$BIN"
pgrep -f "cloudflared.*<name>" > /dev/null || { pkill -f "cloudflared.*<name>" 2>/dev/null; sleep 1; nohup "$BIN" --no-autoupdate tunnel run --credentials-file "$CRED" --url http://<origin> <tunnel-name> >> "$LOG" 2>&1 &; }
```

### Serving Additional Apps (Streamlit, etc.)
Create a systemd user service for the app, then a separate tunnel pointing to `http://127.0.0.1:<PORT>`.

```bash
cat > ~/.config/systemd/user/streamlit-<app>.service << EOF
[Unit]
Description=Streamlit <App>
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
WorkingDirectory=/home/sean/workspace/<path>
ExecStart=/home/sean/workspace/<path>/venv/bin/streamlit run app.py --server.port <PORT> --server.headless true --server.address 127.0.0.1
Restart=always
RestartSec=5
[Install]
WantedBy=default.target
EOF
systemctl --user daemon-reload && systemctl --user enable --now streamlit-<app>
```

### Cloudflare Tunnel Operations

For tunnel binary persistence, systemd user services, auth patterns (cookie-based + Streamlit-internal), WebSocket proxying, ingress config, and key identifiers, see:
- `references/cloudflare-tunnel-ops.md`

## Cloudflare Tunnel Credentials vs Access Tokens

| Token Type | Use for | Cannot do |
|---|---|---|
| `CFAT_TOKEN` (Cloudflare Access Token) | ZT/Access policies, device checks | Create/list tunnels |
| Tunnel Credentials (`credentials.json`) | `cloudflared tunnel run` | Access policies |

**Account ID**: `fd4058c7aa1da2cb3ec2f2c9f028c022`
**Zone ID** (codeovertcp.com): `a0dc1c2d5a810fabb43cb596a7e4b322`

### Active Tunnels (as of June 2026)
| Tunnel | ID | Domain | Origin |
|---|---|---|---|
| hermes-webui | 93328a7a-43ea-4329-99d9-92d9a717dfcc | hermes.codeovertcp.com | 172.19.0.2:8787 |
| onetag-tunnel-new | b02e5bb6-4324-4e40-a624-e21cd128f305 | onetag.codeovertcp.com | 127.0.0.1:8501 |
| agent-os-argo | fe36ddb5-cd10-46ac-8e89-b2763f845153 | agent-os.codeovertcp.com | backend:3001 |