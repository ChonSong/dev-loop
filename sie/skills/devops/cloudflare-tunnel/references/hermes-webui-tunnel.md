# hermes-webui Cloudflare Tunnel — Session Notes

## Current State (May 2026)

| Field | Value |
|---|---|
| Tunnel name | `hermes-webui` |
| Tunnel ID | `93328a7a-43ea-4329-99d9-92d9a717dfcc` |
| Public URLs | `https://hermes.codeovertcp.com`, `https://skills.codeovertcp.com`, `https://wiz.codeovertcp.com` |
| Local URL | `http://172.19.0.2:8787` (container) / `http://localhost:8787` (host) |
| DNS CNAME | `hermes.codeovertcp.com` → `93328a7a-43ea-4329-99d9-92d9a717dfcc.cfargotunnel.com` (proxied) |
| Credentials | `/home/sean/.cloudflared/hermes-webui-creds.json` |
| Token | `/home/sean/.cloudflared/hermes-webui-argo-token.txt` |
| Binary (persistent) | `/home/sean/.hermes/bin/cloudflared` |
| Config | `/home/sean/.hermes/cloudflared/config.yml` |
| Watchdog | `~/.hermes/scripts/hermes-webui-tunnel-watchdog.sh` |
| Log | `/home/sean/.hermes/logs/cloudflared-hermes-webui.log` |

## Cloudflare API Auth

```
X-Auth-Email: Seanos1a@gmail.com
X-Auth-Key: 4551f6bda4835ee658c81221ee8783c9e7af3
Account ID: fd4058c7aa1da2cb3ec2f2c9f028c022
Zone ID (codeovertcp.com): a0dc1c2d5a810fabb43cb596a7e4b322
DNS Record ID (hermes CNAME): 13fb48dbc8771a2dd1beaac9306e03a9
```

## Restart Commands

```bash
# Kill existing
pkill -f "cloudflared.*hermes-webui" 2>/dev/null; sleep 1

# Start with persistent binary + no-autoupdate
nohup /home/sean/.hermes/bin/cloudflared --no-autoupdate tunnel run \
  --credentials-file /home/sean/.cloudflared/hermes-webui-creds.json \
  --url http://172.19.0.2:8787 hermes-webui \
  >> /home/sean/.hermes/logs/cloudflared-hermes-webui.log 2>&1 &

# Verify
sleep 8
pgrep -af "cloudflared.*hermes-webui"
curl -sL -o /dev/null -w "%{http_code}" https://hermes.codeovertcp.com
```

## Recreating the Tunnel (when credentials are stale)

```bash
# 1. Delete old tunnel
curl -s -X DELETE \
  "https://api.cloudflare.com/client/v4/accounts/fd4058c7aa1da2cb3ec2f2c9f028c022/tunnels/<OLD_ID>" \
  -H "X-Auth-Email: Seanos1a@gmail.com" \
  -H "X-Auth-Key: 4551f6bda4835ee658c81221ee8783c9e7af3"

# 2. Create new tunnel (captures credentials_file + token in response)
curl -s -X POST \
  "https://api.cloudflare.com/client/v4/accounts/fd4058c7aa1da2cb3ec2f2c9f028c022/tunnels" \
  -H "X-Auth-Email: Seanos1a@gmail.com" \
  -H "X-Auth-Key: 4551f6bda4835ee658c81221ee8783c9e7af3" \
  -H "Content-Type: application/json" \
  -d '{"name":"hermes-webui"}' > /tmp/tunnel.json

# 3. Extract and upload credentials
python3 -c "
import json
d = json.load(open('/tmp/tunnel.json'))
creds = d['result']['credentials_file']
with open('/tmp/hermes-webui-creds.json', 'w') as f:
    json.dump(creds, f)
token = d['result']['token']
with open('/tmp/hermes-webui-token.txt', 'w') as f:
    f.write(token)
tunnel_id = d['result']['id']
print(f'Tunnel ID: {tunnel_id}')
print(f'Token length: {len(token)}')
"

# 4. Upload to host
scp -i /home/hermeswebui/.hermes/container_key /tmp/hermes-webui-creds.json \
  sean@172.19.0.1:/home/sean/.cloudflared/hermes-webui-creds.json

# 5. Update DNS CNAME
curl -s -X PUT \
  "https://api.cloudflare.com/client/v4/zones/a0dc1c2d5a810fabb43cb596a7e4b322/dns_records/13fb48dbc8771a2dd1beaac9306e03a9" \
  -H "X-Auth-Email: Seanos1a@gmail.com" \
  -H "X-Auth-Key: 4551f6bda4835ee658c81221ee8783c9e7af3" \
  -H "Content-Type: application/json" \
  -d '{"type":"CNAME","name":"hermes","content":"<NEW_TUNNEL_ID>.cfargotunnel.com","proxied":true}'

# 6. Restart tunnel (see above)
```

## Error Diagnosis

### Error 1033 ("Unknown error")
Cloudflare's generic error during Access challenge. Check in order:
1. Is the tunnel process running? `pgrep -af cloudflared`
2. Is the binary still present? `ls -la /home/sean/.hermes/bin/cloudflared`
3. Are credentials current? (tunnel not deleted/recreated since creds were saved)
4. Is DNS pointing to correct tunnel ID?
5. Does the tunnel ingress config include the hostname? (see "HTTP 404 — Tunnel ingress rule missing" below)

### HTTP 404 — "This page can't be found" (browser-native, after CF Access auth)

**Symptom:** User reaches Cloudflare Access login, authenticates, then sees a plain browser 404 page: "No web page was found for the web address: https://hermes.codeovertcp.com/". The 404 comes from the **origin server** through the tunnel, not from Cloudflare's edge.

**Root Causes (in order of likelihood):**

#### Cause A: Tunnel ingress rule missing the hostname (MOST COMMON after tunnel recreation)

The tunnel's remote ingress config routes by hostname. If `hermes.codeovertcp.com` is not in the ingress rules, the tunnel falls through to the catch-all `http_status:404` rule.

**Diagnosis:**
```bash
# Check the tunnel's live ingress config from logs
grep "ingress\|hostname\|Updated to new configuration" /home/sean/.hermes/logs/cloudflared-hermes-webui.log | tail -5

# Or via API
curl -s "https://api.cloudflare.com/client/v4/accounts/fd4058c7aa1da2cb3ec2f2c9f028c022/tunnels/93328a7a-43ea-4329-99d9-92d9a717dfcc" \
  -H "X-Auth-Email: Seanos1a@gmail.com" \
  -H "X-Auth-Key: 4551f6bda4835ee658c81221ee8783c9e7af3" | python3 -c "
import sys,json
d=json.load(sys.stdin)
cfg = d.get('result',{}).get('config',{})
for r in cfg.get('ingress',[]):
    print(r.get('hostname','<catch-all>'), '->', r.get('service'))
"
```

**Fix — Update ingress rules via API (must use `cfd_tunnel` endpoint, NOT `tunnels`):**
```bash
curl -s -X PUT \
  "https://api.cloudflare.com/client/v4/accounts/fd4058c7aa1da2cb3ec2f2c9f028c022/cfd_tunnel/93328a7a-43ea-4329-99d9-92d9a717dfcc/configurations" \
  -H "X-Auth-Email: Seanos1a@gmail.com" \
  -H "X-Auth-Key: 4551f6bda4835ee658c81221ee8783c9e7af3" \
  -H "Content-Type: application/json" \
  -d '{"config":{"ingress":[{"hostname":"hermes.codeovertcp.com","service":"http://172.19.0.2:8787"},{"hostname":"skills.codeovertcp.com","service":"http://172.19.0.2:8787"},{"hostname":"wiz.codeovertcp.com","service":"http://localhost:8080"},{"service":"http_status:404"}]}}'
```

**Important API notes:**
- Correct endpoint: `/accounts/{id}/cfd_tunnel/{id}/configurations` — NOT `/accounts/{id}/tunnels/{id}/configurations` (returns 404)
- Body must be `{"config": {"ingress": [...]}}` — wrapping in `config` is required
- The last rule MUST be `{"service": "http_status:404"}` as catch-all
- Existing remote config is overwritten entirely — include ALL hostnames you need

#### Cause B: Cloudflare Access Application misconfigured or missing

If Cause A is ruled out, the Access application itself may be broken.

**Diagnosis:** `curl -s -o /dev/null -w "%{http_code}" https://hermes.codeovertcp.com/cdn-cgi/access/login` — 404 means the Access application config is broken/missing.

**Fix:** Go to Cloudflare Zero Trust → Access → Applications → Add application → Self-hosted → Domain: `hermes.codeovertcp.com` → Create policy.

#### Cause C: Origin server returns 404 for proxied requests

The origin may reject requests with unexpected `Host` headers or CF-Access redirect paths.

**Diagnosis:** Compare local vs proxied:
```bash
curl -s -o /dev/null -w "Local: %{http_code}\n" http://127.0.0.1:8787/
curl -s -o /dev/null -w "Proxied: %{http_code}\n" https://hermes.codeovertcp.com/
```

If local is 200 but proxied is 404, the issue is in the proxying layer (Causes A or B above), not the app itself.

### Tunnel Dies Repeatedly

**Symptom:** Tunnel works after restart, then dies again hours/days later.

**Root cause (in order of likelihood on this host):**
1. `cloudflared` auto-updater replaced the binary in `/tmp/` (tmpfs), killing the running process. Log signature: `cloudflared has been updated to version X.X.X` followed by `Tunnel server stopped`.
2. Host reboot wiped `/tmp/cloudflared`.
3. Cloudflare edge dropped the tunnel connection (less common; cloudflared reconnects automatically).

**Fix:** See SKILL.md pitfall "Binary stored on `/tmp/`" — use persistent path + `--no-autoupdate` + watchdog with re-download.

## Watchdog Script

Located at: `~/.hermes/scripts/hermes-webui-tunnel-watchdog.sh`

Key features:
- Uses persistent binary at `/home/sean/.hermes/bin/cloudflared` (NOT `/tmp/`)
- Passes `--no-autoupdate` to prevent in-place binary replacement
- Re-downloads binary if missing from persistent storage
- Logs to `/home/sean/.hermes/logs/hermes-webui-tunnel.log`

## Other Tunnels on This Account

| Tunnel | ID | Status (May 2026) |
|---|---|---|
| agent-os-argo | fe36ddb5-cd10-46ac-8e89-b2763f845153 | healthy |
| affine-tunnel | 60942fa2-1a57-430c-b1bf-260ca0e619e6 | down |
| agent-os-final | a74d07d2-0c95-4b25-81c9-68345cca97f3 | down |
| agent-os-nano | 0e303e27-ed27-48fe-98d2-f729160de07a | down |

## Cloudflare API Token Types and Limitations (June 2026)

| Token | Prefix | Can Manage | Cannot |
|---|---|---|---|
| Zone DNS Token | `cfut_` | DNS records (CNAME, A, etc.) — full CRUD | Tunnel config, tunnel routes |
| Tunnel Account Token | `cfat_` | Read tunnel info (`GET /tunnels/:id`), **Create tunnels** (`POST /accounts/{id}/tunnels`) | Write tunnel config (`PUT/POST /configurations`), returns error 10405 |
| Global API Key | (32+ hex chars) | Full account management (if valid) | — |
| Argo Tunnel Token | base64 JSON | Nothing via API (not a CF API token) | All API endpoints reject it |

**Important:** The `4551f6bda4835ee658c81221ee8783c9e7af3` key is NOT a valid Global API Key (rejected with `6103: Invalid format`). The argo tokens (`eyJhIj...`) are base64-encoded `{account, tunnel_id, secret}` — not API tokens.

**`cfat_` token CAN create tunnels:**
```bash
curl -s -X POST \
  "https://api.cloudflare.com/client/v4/accounts/{account_id}/tunnels" \
  -H "Authorization: Bearer cfat_..." \
  -H "Content-Type: application/json" \
  -d '{"name": "my-tunnel"}'
```
Response includes `credentials_file` (with AccountTag, TunnelID, TunnelName, TunnelSecret) and `token` (the argo token). **Capture both immediately** — the token is NOT available from any other endpoint.

**`cfat_` token CANNOT write tunnel config:**
- `PUT /accounts/{id}/cfd_tunnel/{id}/configurations` → error 10405
- `PUT /accounts/{id}/tunnels/{id}/configurations` → error 10405
- `PATCH /accounts/{id}/tunnels/{id}` → error 10405

**Verified working for DNS record creation:**
```bash
curl -s -X POST \
  "https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records" \
  -H "Authorization: Bearer cfut_..." \
  -H "Content-Type: application/json" \
  -d '{"type":"CNAME","name":"SUB","content":"TUNNEL_ID.cfargotunnel.com","ttl":1,"proxied":true}'
```

## Other Tunnels on This Account (June 2026)

| Tunnel | ID | Status | Notes |
|---|---|---|---|
| hermes-webui | 93328a7a-43ea-4329-99d9-92d9a717dfcc | healthy | Main tunnel, port 8787. Routes: hermes/skills/wiz.codeovertcp.com |
| onetag-tunnel-v2 | b3200be4-a8a8-4381-980b-038e402d8702 | healthy | Streamlit tunnel, port 8501. Routes: onetag.codeovertcp.com |
| agent-os-argo | fe36ddb5-cd10-46ac-8e89-b2763f845153 | healthy | agent-os backend |
| agent-os-final | a74d07d2-0c95-4b25-81c9-68345cca97f3 | down | Stale — do NOT reference in config.yml |
| affine-tunnel | 60942fa2-1a57-430c-b1bf-260ca0e619e6 | down | |
| agent-os-nano | 0e303e27-ed27-48fe-98d2-f729160de07a | down | |

**WARNING:** The old `config.yml` used tunnel ID `a74d07d2` (agent-os-final) instead of `93328a7a` (hermes-webui). This caused connections to fail with `Unauthorized: Invalid tunnel secret`. Always verify the tunnel ID matches the credentials file.

## onetag.codeovertcp.com (June 2026) — LIVE ✅

**Current tunnel:** `onetag-tunnel-new` (ID: `b02e5bb6-4324-4e40-a624-e21cd128f305`)
- Replaces old `onetag-tunnel-v2` (ID: `b3200be4`) which was deleted and recreated

**Setup:**
1. Streamlit app runs on `127.0.0.1:8502` (internal, systemd: `streamlit-onetag`)
2. Auth wrapper runs on `127.0.0.1:8501` (systemd: `auth-wrapper-onetag`)
3. Cloudflare tunnel forwards `onetag.codeovertcp.com` → `http://127.0.0.1:8501`
4. Cloudflare Access app for onetag was DELETED (conflicted with Basic Auth)

**Auth:**
- Username: `sa`
- Password: `dawnofdarren`
- Method: HTTP Basic Auth via Python proxy wrapper

**DNS:** `e047a89ea069398294b17e69cda3d8d0` (CNAME → `b02e5bb6.cfargotunnel.com`)

**Credentials:**
- `/home/sean/.hermes/cloudflared/onetag-tunnel-creds.json` (persistent storage)
- **NOT** in `/home/sean/.cloudflared/` (restricted permissions, scp fails)

**Files:**
- App: `/home/sean/workspace/forrest-plan-and-track/streamlit_onetag/app.py`
- Auth wrapper: `/home/sean/workspace/forrest-plan-and-track/streamlit_onetag/auth_wrapper.py`

**Lessons learned:**
- CF Access app intercepts requests BEFORE origin-level Basic Auth — must delete CF Access app if using Basic Auth at origin
- Browser `ERR_TOO_MANY_RETRIES` on 401 is caused by conflicting auth layers, not the 401 itself
- Systemd `Requires=` + `After=` chains work but need absolute venv Python paths
- `scp` to `~/.cloudflared/` fails; write files via `ssh` heredoc or use `~/.hermes/cloudflared/`