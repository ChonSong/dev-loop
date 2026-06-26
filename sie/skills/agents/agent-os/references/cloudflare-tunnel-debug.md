# Cloudflare Tunnel Debugging Reference

## Critical: trycloudflare.com URLs Are NOT Stable

Named tunnels (`cloudflared tunnel run --token-file`) use `*.trycloudflare.com` subdomains that **change every tunnel restart**. The URL is printed once at startup and never again.

**Impact for CI:** The `DEPLOY_HOST` GitHub secret becomes stale after every cloudflared restart. CI calls `https://${DEPLOY_HOST}/api/deploy` but gets "Could not resolve host".

**Diagnosing:**
```
* Could not resolve host: fe36ddb5-cd10-46ac-8e89-b2763f845153.trycloudflare.com
```
Cloudflared may still be connected (4 `Registered tunnel connection` logs in Sydney), but DNS has rotated.

**Get current URL:**
```bash
# Via Cloudflare API (needs CF_API_TOKEN with tunnels:read):
curl -s "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/cfd_tunnel/${TUNNEL_ID}" \
  -H "Authorization: Bearer ${CF_API_TOKEN}" | python3 -c \
  "import json,sys; d=json.load(sys.stdin); [print(c['colo_name'], c['uuid']) for c in d['result']['connections']]"

# Inside container (metrics port):
docker exec agent-os-cloudflared curl -s http://localhost:20241/quicktunnel
```

**Long-term fix:** CNAME `*.your-domain.com` → `<tunnel_id>.cfargotunnel.com`. Tunnel ID is stable; only the CNAME target matters.

## Critical: `cfdtunnel.com` Does NOT Resolve

Only `cfargotunnel.com` works. The `cfdtunnel.com` DNS suffix (sometimes shown in older docs or `cfd_tunnel` tunnel type) produces HTTP 530/1016 — the domain does not resolve publicly.

Always use `argo_tunnel` tunnel type and `cfargotunnel.com` in DNS targets.

## Error: "error decoding origin cert: missing token in the certificate"

**Root cause:** The origin certificate from **SSL/TLS → Origin Server** (dashboard) is a plain TLS cert. `cloudflared tunnel run` needs a cert with an embedded `ARGO TUNNEL TOKEN` PEM block.

**Two fixes:**
- `cloudflared login` — browser-based, generates correct cert with embedded token
- `--token-file <JWT>` — tunnel token from API bundles credentials + cert; no cert.pem needed

## Token Types (verified correct)

| Prefix/Format | Type | Works with `cloudflared tunnel run`? |
|---|---|---|
| `cfat_...` | Cloudflare Access/Zero Trust API token | ❌ Only for Cloudflare API calls (create tunnel, DNS) |
| `eyJ...` (240+ byte JWT) | Argo Tunnel token (from API `created_token`) | ✅ `--token-file` or `--token` |
| `AccountTag`/`TunnelID`/`TunnelSecret` (camelCase JSON) | Credentials file from API response | ✅ With `--credentials-file` |
| `account_tag`/`tunnel_id`/`tunnel_secret` (lowercase JSON) | Credentials file format (older/dashboard) | ✅ |

**Common mistakes:**
- Using `cfat_` (Access token) with `--token` → `Provided Tunnel token is not valid`
- Using `cfut_...` → not a valid Cloudflare token prefix; likely a misread token type
- Downloading tunnel credentials from dashboard → may give lowercase JSON; API `created_token` response gives camelCase

## Credentials File Format

The API returns **camelCase** keys (`AccountTag`, `TunnelID`, `TunnelSecret`):
```json
{
  "AccountTag": "<cloudflare-account-id>",
  "TunnelID": "<tunnel-uuid>",
  "TunnelSecret": "<base64-secret>"
}
```

Dashboard downloads may give **lowercase** (`account_tag`, `tunnel_id`, `tunnel_secret`). Both work with modern cloudflared.

## cloudflared 2026.3.0 Flags

```
# --token-file (recommended) — bundles credentials + cert; no separate cert.pem
cloudflared tunnel run --token-file /path/to/agent-os-argo-token.txt --url http://localhost:8900

# --token — inline JWT
cloudflared tunnel run --token <JWT> --url http://localhost:8900

# --credentials-file — separate credentials JSON + --origincert (older pattern)
cloudflared tunnel run --credentials-file /path/to/creds.json --origincert /path/to/cert.pem
```

## Quick Test Commands

```bash
# Check cloudflared version
~/bin/cloudflared --version

# Verify tunnel token file size (should be ~240 bytes for valid JWT)
ls -la ~/.cloudflared/agent-os-argo-token.txt

# Run tunnel with log output
nohup ~/bin/cloudflared tunnel run --token-file ~/.cloudflared/agent-os-argo-token.txt \
  --url http://localhost:8900 > /tmp/cloudflared.log 2>&1 &

# Check tunnel logs
cat /tmp/cloudflared.log

# Test public endpoint
curl -s https://nanobot.codeovertcp.com/health
```

## DNS: CNAME Target Format

When creating a DNS CNAME for a tunnel:
```
CNAME: nanobot.codeovertcp.com → <tunnel_id>.cfargotunnel.com (proxied)
```
Not `cfdtunnel.com` — only `cfargotunnel.com` resolves.

## Verify Token Zone Access Before Creating DNS

A `cfut_` API token may be scoped to only specific zones. `agent-os.chonsong.com` and `agent-os.codeovertcp.com` may be in DIFFERENT zones.

**Always verify zone access first:**
```python
import urllib.request, json, ssl

token = 'cfut_...'  # the token to test
ctx = ssl.create_default_context()
req = urllib.request.Request('https://api.cloudflare.com/client/v4/zones')
req.add_header('Authorization', 'Bearer ' + token)
resp = urllib.request.urlopen(req, timeout=8, context=ctx)
zones = json.loads(resp.read())['result']
for z in zones:
    print(z['name'], z['id'], z['account']['name'])
# Output: chonsong.com has zone ID X, codeovertcp.com has zone ID Y
# If only codeovertcp.com appears, you CANNOT create DNS for chonsong.com
```

**Symptom of wrong zone:** DNS API returns `{"success": false, "errors": [{"code": 10000, "message": "zone_not_found"}]}`.
