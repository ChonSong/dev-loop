# Testing Cloudflare API Tokens

Protocol for testing unknown Cloudflare credentials against the DNS management API.

## Why This Exists

Cloudflare has multiple token formats with overlapping scopes:
- `cfat_` tokens are API tokens (may or may not have DNS scope)
- `cfut_` tokens are tunnel tokens (some can do DNS, some can't)
- Global API keys use `X-Auth-Email` + `X-Auth-Key` headers (NOT Bearer)
- Argo tunnel base64 tokens (from cert.pem) are tunnel-only

You can't tell from the prefix alone. **Test first.**

## The Test Script

```python
import json, urllib.request, urllib.error

ZONE_ID = "a0dc1c2d5a810fabb43cb596a7e4b322"  # codeovertcp.com zone

def test_token(label, token, use_global=False):
    url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records?per_page=1"
    req = urllib.request.Request(url)
    if use_global:
        req.add_header("X-Auth-Email", "account@example.com")  # Fill in
        req.add_header("X-Auth-Key", token)
    else:
        req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            body = json.loads(resp.read())
            if body.get("success"):
                print(f"  ✅ {label} — works for DNS")
            else:
                err = body.get("errors", [{}])[0]
                print(f"  ❌ {label} — {err.get('message', 'unknown')} (code {err.get('code', '?')})")
    except urllib.error.HTTPError as e:
        body = json.loads(e.read())
        err = body.get("errors", [{}])[0]
        print(f"  ❌ {label} — HTTP {e.code}: {err.get('message', 'unknown')} (code {err.get('code', '?')})")
```

## Response Codes

| Code | Meaning | Next Step |
|------|---------|-----------|
| 200  | Token works for DNS | Use it |
| 400 (9106) | Auth format or token wrong | Try different token or auth method |
| 401 (10000) | Token invalid/expired | Rotate or obtain new token |
| 403  | Token valid but lacks scope | Need Zone:DNS:Edit permission |

## Examples (from real testing, June 2026)

```
=== cfat_ (API Token) ===
  ✅ WORKS (HTTP 200)

=== cfut_ (Tunnel Token, broad scope) ===
  ✅ WORKS (HTTP 200)

=== Global Key (short hex, `4551f6b...`) ===
  ❌ Fail (HTTP 400): Authentication failed (code 9106)

=== Global Key (long complex, `9P5Sr_...`) ===
  ❌ Fail (HTTP 401): Authentication error (code 10000)
```

## Saving Working Tokens

Once a token is confirmed working, save it to `.env`:

```bash
echo 'CLOUDFLARE_API_TOKEN=cfat_...' >> /home/sc/.hermes/.env
```

Both working tokens from this session are saved at `/home/sc/.hermes/.env` (lines 28-29):
- `CLOUDFLARE_API_TOKEN` — cfat token, best for DNS management
- `CLOUDFLARE_TUNNEL_TOKEN` — cfut token, also works for DNS

## Cert.pem Decoding

The tunnel cert at `~/.cloudflared/cert.pem` is a base64 JWT containing zone/account IDs:

```python
import base64, json
lines = open('/home/sc/.cloudflared/cert.pem').read().strip().split('\n')
b64 = ''.join(l for l in lines if l and not l.startswith('---'))
padded = b64 + '=' * (4 - len(b64) % 4) if len(b64) % 4 else b64
print(json.loads(base64.b64decode(padded)))
```

Returns: `{"zoneID": "...", "accountID": "...", "apiToken": "cfut_..."}`

**The apiToken in cert.pem is a tunnel-scoped cfut_ — it likely won't work for DNS.** Use a proper cfat_ token instead.
