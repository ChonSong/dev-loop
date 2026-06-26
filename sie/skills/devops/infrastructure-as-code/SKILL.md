---
name: infrastructure-as-code
description: Terraform workflows for Cloudflare, AWS, and server provisioning. Covers terraform init/plan/apply, Cloudflare tunnel + Access policy, state management, and GitOps patterns for infrastructure as code.
tags: ["terraform", "cloudflare", "iac", "infrastructure", "dns", "vpn", "tunnel"]
---

# Infrastructure as Code

## Host Environment

The host (hpprobook) does NOT have Terraform installed. For Terraform operations, use Python/scripting approach OR install Terraform to user directory.

### Install Terraform (no sudo needed)

```bash
ssh -o StrictHostKeyChecking=no sean@localhost "mkdir -p ~/.local/bin && curl -fsSL https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip -o /tmp/terraform.zip && unzip -o /tmp/terraform.zip -d ~/.local/bin && chmod +x ~/.local/bin/terraform && ~/.local/bin/terraform version"
```

## Cloudflare Zero Trust MCP Server (alternative to cloudflared CLI)

For programmatic tunnel and Access policy management, use the Cloudflare Zero Trust MCP server instead of cloudflared CLI. It wraps Cloudflare API v4 directly and supports Access policies, service tokens, and tunnel CRUD.

**Location (verified on disk):**
```
/opt/data/agent-os/packages/mcp-servers/cloudflare-zero-trust/
  SKILL.md          — skill documentation
  server.py         — MCP server (11 tools)
  requirements.txt  — httpx, uvicorn, asgiref
```

**Capabilities:**
- Tunnel CRUD (`tunnel_create`, `tunnel_delete`, `tunnel_list`, `tunnel_inspect`)
- DNS routing (`tunnel_route_dns`, `tunnel_delete_dns`)
- Access policy CRUD (`access_policy_list`, `access_policy_create`, `access_policy_delete`)
- Access app registration (`access_app_create`, `access_app_delete`)

**Setup:** Requires `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID` env vars. Token needs `Account: Tunnels: Edit`, `Account: Access: Policies: Edit`, `Account: Access: Service Tokens: Edit`.

**Running the server:**
```bash
cd /opt/data/agent-os/packages/mcp-servers/cloudflare-zero-trust
pip install -r requirements.txt
CLOUDFLARE_API_TOKEN=... CLOUDFLARE_ACCOUNT_ID=... python server.py --port 9000
```

**Adding to Hermes (via native-mcp skill):**
```bash
hermes config add mcp-server cloudflare-zero-trust \
  --type stdio \
  --command python \
  --args server.py \
  --cwd /opt/data/agent-os/packages/mcp-servers/cloudflare-zero-trust \
  --env CLOUDFLARE_API_TOKEN \
  --env CLOUDFLARE_ACCOUNT_ID
```

**Key advantage over cloudflared CLI:** Access policy management (identity-based access rules, service tokens, device posture) is only available via API — cloudflared CLI cannot manage Access policies. Use the MCP server for full zero-trust config.

## Cloudflare Tunnel Setup (cloudflared binary)

cloudflared may not be in PATH. Verify before use:
```bash
which cloudflared  # empty if not installed
/tmp/cloudflared --version  # ad-hoc install location
```

### Tunnel creation via Cloudflare API (recommended)

Do NOT rely on `cloudflared tunnel create` interactively. Use the Cloudflare API:

```bash
# 1. Create tunnel
TUNNEL_RESP=$(curl -s -X POST "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/tunnels" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"$TUNNEL_NAME\", \"tunnel_type\": \"cfd_tunnel\"}")

# 2. Parse response
TUNNEL_ID=$(echo "$TUNNEL_RESP" | python3 -c "import json,sys; print(json.load(sys.stdin)['result']['id'])")
TUNNEL_TOKEN=$(echo "$TUNNEL_RESP" | python3 -c "import json,sys; print(json.load(sys.stdin)['result'].get('token','N/A'))")
echo "TunnelID: $TUNNEL_ID"

# 3. Save credentials file (embedded in API response)
echo "$TUNNEL_RESP" | python3 -c "import json,sys; json.dump(json.load(sys.stdin)['result']['credentials_file'], open('/opt/data/cloudflared/credentials.json','w'))"

# 4. Route DNS
curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"type\":\"CNAME\",\"name\":\"subdomain\",\"content\":\"${TUNNEL_ID}.cfargotunnel.com\",\"proxied\":true}"

# 5. Run tunnel
cloudflared tunnel --config /opt/data/cloudflared/config.yml run
```

### cloudflared config.yml format

```yaml
tunnel: <tunnel-uuid>
credentials-file: /path/to/credentials.json

ingress:
  - hostname: yourdomain.com
    service: http://localhost:8642
  - hostname: '*.yourdomain.com'
    service: http://localhost:8642
  - service: http_status:404
```

**Critical:** `tunnel:` field is required when using a credentials file. Without it, cloudflared errors: `"cloudflared tunnel run" requires the ID or name of the tunnel`.

**Token format gotcha**

| Token prefix | Type | Works with `tunnel run --token`? | Can manage tunnels via API? |
|---|---|---|---|
| `cfut_` | Unified Tunnel token | Yes | No — use dashboard or API with Account token |
| `cfat_` | Cloudflare Access API token | No — for Access API calls only | No — wrong API surface |

**If only a `cfat_` token is available:**
1. The token CAN be used to call Cloudflare Access API (`/client/v4/accounts/{id}/access/...`) but NOT Tunnel API (`/client/v4/accounts/{id}/tunnels/...`)
2. For tunnel management, either get a proper Cloudflare API token with `Account: Tunnels: Edit` scope, OR create the tunnel in the dashboard and use the resulting `--token` credential file directly
3. Cloudflare Zero Trust MCP server (see below) is the programmatic alternative to cloudflared CLI when API access is available

## Host-level cloudflared for Docker Service Exposure

When the target service (e.g. hermes-webui) is a Docker container exposing only `127.0.0.1:8787` (localhost-only), running cloudflared as a **host systemd service** (rather than inside a Docker container) is the correct approach — it can reach the host's localhost:8787 while the tunnel process itself remains on the host.

**Architecture:**
```
hermes.codeovertcp.com
    ↓ HTTPS + Cloudflare Access
cloudflared (host systemd) → http://localhost:8787 (hermes-webui container via host network)
```

**Step-by-step (when Cloudflare API token is available):**

```bash
# 1. Create tunnel via API
TUNNEL_RESP=$(curl -s -X POST "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/tunnels" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"hermes-webui","tunnel_type":"cfd_tunnel"}')
TUNNEL_ID=$(echo "$TUNNEL_RESP" | python3 -c "import json,sys; print(json.load(sys.stdin)['result']['id'])")

# 2. Save credentials file
echo "$TUNNEL_RESP" | python3 -c "import json,sys; json.dump(json.load(sys.stdin)['result']['credentials_file'], open('/home/sean/.cloudflared/hermes-webui-creds.json','w'))"

# 3. Write config
cat > /home/sean/.cloudflared/hermes-webui.yml << 'EOF'
tunnel: <TUNNEL_ID>
credentials-file: /home/sean/.cloudflared/hermes-webui-creds.json
ingress:
  - hostname: hermes.codeovertcp.com
    service: http://localhost:8787
  - service: http_status:404
EOF

# 4. Create DNS CNAME
curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"CNAME","name":"hermes","content":"'"$TUNNEL_ID"'.cfargotunnel.com","proxied":true}'

# 5. Run cloudflared
cloudflared --config /home/sean/.cloudflared/hermes-webui.yml run
```

**Step-by-step (when only a tunnel token from dashboard is available):**

```bash
# Token from dashboard: eyJh...== (cfut_ prefix format)
# Save to token file
echo "eyJh...==" > /home/sean/.cloudflared/hermes-webui-token.txt

# Run directly with token
cloudflared tunnel run --token-file /home/sean/.cloudflared/hermes-webui-token.txt --url http://localhost:8787
```

**Adding cloudflared to an existing Docker Compose stack (hermes-webui):**

hermes-webui runs in the `hermes-webui_default` Docker network with `127.0.0.1:8787` published. To expose it:
1. cloudflared runs on the host (not in a container) so it can reach `localhost:8787`
2. The DNS CNAME must point to the tunnel's `*.cfargotunnel.com` address (not a fixed IP)
3. If migrating from existing `webui.codeovertcp.com` CNAME to `hermes.codeovertcp.com`, update the DNS record to the new tunnel ID

> **Live reference:** `references/cloudflared-tunnel-setup.md` — working end-to-end session transcript with verified config.yml contents, credentials.json structure, and Cloudflare API endpoint inventory.
> **Tunnel failures:** `references/cloudflared-tunnel-failures.md` — stale credentials → `control stream encountered a failure while serving` loop, token vs credentials file confusion, and session transcript of the 2026-05-26 outage.
> **Access app setup:** `references/cloudflare-access-app-setup.md` — IdP linkage (allowed_idps PUT vs PATCH), tunnel secret mismatch fix (API PATCH), Access app verification, and watchdog script for no-sudo persistence.

## Troubleshooting: 502 Bad Gateway with a Healthy Tunnel

**Symptom:** `curl -sI https://hermes.codeovertcp.com` returns HTTP/2 302 (Access redirect working), but actual browser access returns 502 Bad Gateway.

**Root cause:** Multiple cloudflared processes running with the **same tunnel credentials**. Cloudflare shows the tunnel as "healthy" but routing fails because two processes fight over the tunnel control stream.

**Debugging sequence:**
```bash
# 1. Check tunnel status (healthy ≠ working if multiple processes)
curl -s "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/cfd_tunnel/$TUNNEL_ID" \
  -H "X-Auth-Key: $GLOBAL_API_KEY" -H "X-Auth-Email: $CF_EMAIL" | \
  python3 -c "import json,sys; t=json.load(sys.stdin)['result']; print('Status:', t['status'], '| Conn:', t.get('num_connections'))"

# 2. Check for duplicate cloudflared processes
pgrep -fa cloudflared  # or: ps aux | grep cloudflared

# 3. Kill ALL cloudflared processes before starting a clean one
pkill -f cloudflared; sleep 2

# 4. Verify target is reachable from host
curl --max-time 5 http://172.19.0.2:8787 | head -1

# 5. Start fresh tunnel process with logging
/tmp/cloudflared tunnel run \
  --credentials-file /opt/data/cloudflared/hermes-webui-creds.json \
  --url http://172.19.0.2:8787 hermes-webui \
  >> /tmp/hermes-tunnel.log 2>&1 &

# 6. Watch tunnel logs
sleep 8 && tail /tmp/hermes-tunnel.log

# 7. Confirm Access redirect (should be 302 to cloudflareaccess.com)
curl -sI https://hermes.codeovertcp.com | head -3
```

**Key distinction:**
- `healthy | Connections: N` from API → tunnel registration is working
- `HTTP/2 302` + `www-authenticate: Cloudflare-Access` → Access layer is active
- `HTTP/2 502` → **Access is failing** (tunnel conflict, misconfigured policy, or IdP not linked)

**Why tunnel health ≠ Access health:** A tunnel can register with Cloudflare edge (healthy) while the Access layer still returns 502 due to duplicate processes, wrong origin URL, or a policy misconfiguration. Always check both independently.

## Multiple cloudflared processes = 502 even with healthy tunnel

Running **more than one** cloudflared process with the same tunnel credentials causes a "control stream encountered a failure while serving" cascade — Cloudflare shows "healthy | Connections: N" but actual browser traffic gets 502.

**Symptoms:**
- `curl -sI https://hermes.codeovertcp.com` returns `HTTP/2 302` + Access redirect (looks fine)
- Browser reaches Access login, authenticates with email OTP successfully
- After login: **502 Bad Gateway** from Cloudflare edge
- Tunnel log shows `ERR failed to serve tunnel connection` / `control stream encountered a failure` / `context canceled`
- Cloudflare dashboard shows tunnel as **"healthy | Connections: 8"** — misleading

**Diagnosis:**
```bash
# 1. Check tunnel status
curl -s "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/tunnels" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" | \
  python3 -c "import json,sys; [print(t['name'], t['id'], t['status']) for t in json.load(sys.stdin)['result']]"

# 2. Verify credentials match — compare TunnelID in creds file vs API response
python3 -c "import json; d=json.load(open('/home/sean/.cloudflared/hermes-webui-creds.json')); print('Creds TunnelID:', d['TunnelID'])"

# 3. If TunnelID in creds doesn't appear in API list → stale credentials → tunnel was recreated, creds need updating

# 4. Check for duplicate cloudflared processes
pgrep -la cloudflared

# If duplicates found, kill ALL (zombies need -9 on each PID)
pkill -f cloudflared; sleep 2
pgrep -la cloudflared
# If zombies remain: kill -9 <pid> for each individually

pgrep -la cloudflared || echo "CLEAN"

# Start ONE fresh tunnel with logging
/tmp/cloudflared tunnel run \
  --credentials-file /opt/data/cloudflared/hermes-webui-creds.json \
  --url http://172.19.0.2:8787 hermes-webui \
  >> /tmp/hermes-tunnel.log 2>&1 &

sleep 8 && tail /tmp/hermes-tunnel.log
```

**Rule: one process per tunnel credential file, always.** Kill old before starting new.

## Host-level cloudflared via systemd user service (no-sudo approach)

When you cannot write to `/etc/` (no sudo) and the target service is a Docker container on a private network (e.g. `127.0.0.1:8787` localhost-only), a **systemd user-level service** is the correct approach. This persists across reboots via `enable`.

**Architecture:**
```
hermes.codeovertcp.com
    ↓ HTTPS + Cloudflare Access
cloudflared (host systemd) → http://host-ip:8787 (Docker bridge 172.19.0.x)
```

**Service file:** `~/.config/systemd/user/hermes-webui-tunnel.service`
```ini
[Unit]
Description=Cloudflare Tunnel for hermes-webui
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/home/sean/.local/bin/cloudflared tunnel run \
  --credentials-file /home/sean/.cloudflared/hermes-webui-creds.json \
  --url http://172.19.0.2:8787 hermes-webui
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=default.target
```

**Key notes:**
- `WantedBy=default.target` (not `multi-user.target`) — user-level services don't have a login requirement via `loginctl enable-linger`
- cloudflared binary should be in `~/.local/bin/` (NOT `/tmp/` — tmpfs wipes on reboot)
- `systemctl --user enable hermes-webui-tunnel` — survives reboots
- `systemctl --user start hermes-webui-tunnel` — start immediately
- cloudflared reaches Docker containers via the bridge gateway (e.g. `172.19.0.2`)

**Binary install (no sudo):**
```bash
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
  -o ~/.local/bin/cloudflared
chmod +x ~/.local/bin/cloudflared
```

**Persistence when DBUS is unavailable:** If `systemctl --user` fails (no user DBUS, e.g. in an agent container or SSH session without a logind lingers), use the restart script instead:
```bash
# Run every 5 minutes via cron (crontab -e)
LOG=/opt/data/logs/hermes-webui-tunnel.log */5 * * * * /opt/data/scripts/hermes-webui-tunnel-restart.sh

# Or start manually (for testing)
LOG=/tmp/hermes-tunnel.log /opt/data/scripts/hermes-webui-tunnel-restart.sh
```
The script (`scripts/hermes-webui-tunnel-restart.sh`) checks if the tunnel is running and restarts it only if dead — idempotent, safe to re-run.

## Global API Key as authentication fallback

When `CFAT_TOKEN` (prefix `cfat_`) returns 9109 on tunnel API calls, the user's **Global API Key + email** works as a fallback for all API operations including tunnel creation, DNS management, and Access policy CRUD.

**Usage:**
```bash
curl -s -X POST "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/tunnels" \
  -H "X-Auth-Key: $GLOBAL_API_KEY" \
  -H "X-Auth-Email: seanos1a@gmail.com" \
  -H "Content-Type: application/json" \
  -d '{"name":"hermes-webui","tunnel_type":"cfd_tunnel"}'
```

Global API Key is NOT a bearer token — it uses `X-Auth-Key` and `X-Auth-Email` headers instead of `Authorization: Bearer`.

## Terraform Workflow

### Initialize

```bash
ssh -o StrictHostKeyChecking=no sean@localhost "cd /home/sean/.hermes/agent-os/infra/terraform && ~/.local/bin/terraform init"
```

### Plan

```bash
ssh -o StrictHostKeyChecking=no sean@localhost "cd /home/sean/.hermes/agent-os/infra/terraform && TF_VAR_cloudflare_api_token=<token> TF_VAR_cloudflare_account_id=<id> TF_VAR_zone_id=<zone> TF_VAR_tunnel_secret=<secret> ~/.local/bin/terraform plan"
```

### Apply

```bash
ssh -o StrictHostKeyChecking=no sean@localhost "cd /home/sean/.hermes/agent-os/infra/terraform && TF_VAR_cloudflare_api_token=<token> TF_VAR_cloudflare_account_id=<id> TF_VAR_zone_id=<zone> TF_VAR_tunnel_secret=<secret> ~/.local/bin/terraform apply"
```

## Cloudflare API Token Scopes

Required for Terraform:
- `Account: Tunnel: Edit`
- `Zone: DNS: Edit`
- `Access: Organisations: Read`
- `Access: Applications: Edit`

## Terraform State

Never commit `.tfstate` to git. State is stored locally on the host at:
`/home/sean/.hermes/agent-os/infra/terraform/.terraform/terraform.tfstate`

## Secrets Management

- Cloudflare API token: set via `TF_VAR_cloudflare_api_token` env var
- Tunnel secret: set via `TF_VAR_tunnel_secret` env var
- Never hardcode in `.tfvars` files committed to git

## GitOps Pattern for agent-os

1. Terraform files live in `infra/terraform/` (committed to GitHub)
2. `.tfvars` with real secrets stay on host ONLY (in `.gitignore`)
3. GitHub Actions does NOT run terraform (no credentials in GitHub)
4. Terraform apply runs locally on host when needed
5. Cloudflare tunnel credentials written directly to `~/.cloudflared/`
