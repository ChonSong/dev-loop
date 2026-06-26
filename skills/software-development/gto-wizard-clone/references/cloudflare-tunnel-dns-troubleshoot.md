# Cloudflare Tunnel DNS Troubleshooting (June 2026)

## Symptom

```
https://wiz.codeovertcp.com/gto/training → HTTP 530 "error code: 1033"
```

## Diagnosis

### Step 1: Check tunnel status

```python
import urllib.request, json
ACCOUNT = "fd4058c7aa1da2cb3ec2f2c9f028c022"
req = urllib.request.Request(
    f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT}/tunnels",
    headers={"X-Auth-Email": "seanos1a@gmail.com", "X-Auth-Key": "4551f6bda4835ee658c81221ee8783c9e7af3"})
resp = urllib.request.urlopen(req)
for t in json.loads(resp.read()).get('result', []):
    print(f"{t['name']:25s} {t['id'][:20]:20s} status={t.get('status','?'):12s}")
```

Look for the tunnel with `status=healthy`. There are usually 3+ GTO-related tunnels:

| Name | ID | Status |
|------|-----|--------|
| gto-wizard | 24362d8c-acda-43ca-87d7-9f422b631b11 | down |
| **gto-wizard-clone** | **d828b66a-192c-4230-814e-538f79006519** | **healthy** |
| gto-wizard-v2 | 92674c6b-d706-4639-a403-89706fe5782b | down |

Only the tunnel with `status=healthy` will serve traffic.

### Step 2: Check which tunnel DNS points to

```python
ZONE = "a0dc1c2d5a810fabb43cb596a7e4b322"
dns_req = urllib.request.Request(
    f"https://api.cloudflare.com/client/v4/zones/{ZONE}/dns_records?name=wiz.codeovertcp.com",
    headers={"X-Auth-Email": "...", "X-Auth-Key": "..."})
dns_data = json.loads(urllib.request.urlopen(dns_req).read())
r = dns_data['result'][0]
print(f"Current: {r['content']}")
# Expected: d828b66a-...cfargotunnel.com
```

### Step 3: Fix DNS if it points to wrong tunnel

```python
tunnel_id = "d828b66a-192c-4230-814e-538f79006519"  # the healthy one
body = json.dumps({
    "type": "CNAME", "name": "wiz.codeovertcp.com",
    "content": f"{tunnel_id}.cfargotunnel.com",
    "ttl": 1, "proxied": True
}).encode()
req = urllib.request.Request(
    f"https://api.cloudflare.com/client/v4/zones/{ZONE}/dns_records/{r['id']}",
    data=body,
    headers={"X-Auth-Email": "...", "X-Auth-Key": "...", "Content-Type": "application/json"},
    method="PUT")
result = json.loads(urllib.request.urlopen(req).read())
print(f"DNS update: {'SUCCESS' if result.get('success') else 'FAILED'}")
```

### Step 4: Verify ingress config

```python
config_req = urllib.request.Request(
    f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT}/cfd_tunnel/{tunnel_id}/configurations",
    headers={"X-Auth-Email": "...", "X-Auth-Key": "..."})
config = json.loads(urllib.request.urlopen(config_req).read())
ingress = config['result']['config']['ingress'][0]
print(f"Ingress: {ingress['service']} for {ingress.get('hostname','?')}")
# Must have the correct hostname AND the correct service URL
```

### Step 5: Update ingress config if wrong

```python
body = json.dumps({
    "config": {
        "ingress": [
            {"hostname": "wiz.codeovertcp.com", "service": "http://172.19.0.2:8564"},
            {"service": "http_status:404"}
        ],
        "warp-routing": {"enabled": False}
    }
}).encode()
update_req = urllib.request.Request(
    f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT}/cfd_tunnel/{tunnel_id}/configurations",
    data=body,
    headers={"X-Auth-Email": "...", "X-Auth-Key": "...", "Content-Type": "application/json"},
    method="PUT")
result = json.loads(urllib.request.urlopen(update_req).read())
print(f"Config update version: {result['result']['version']}")
```

The tunnel picks up config changes within ~30 seconds without restart.

## Why Multiple Tunnels?

- `gto-wizard` (24362d8c...): Original tunnel, created by `create_gto_tunnel_v2.py`. Credentials stored on host at `/home/sean/.cloudflared/gto-wizard.json`.
- `gto-wizard-clone` (d828b66a...): The actual running tunnel. Credentials at `/home/hermeswebui/.cloudflared/gto-wizard-creds.json`.
- `gto-wizard-v2` (92674c6b...): Second attempt. Credentials at `...gto-wizard-v2-creds.json`.

The names are misleading and don't reflect which tunnel is actually working. Always check `status` via API.

## Credential Verification

```python
with open("/home/hermeswebui/.cloudflared/gto-wizard-creds.json") as f:
    creds = json.load(f)
print(f"Creds TunnelID: {creds['TunnelID']}")
print(f"Creds Account:  {creds['AccountTag']}")
# Must match the tunnel ID and account tag from Step 1
```

## Quick Reference

```bash
# API Key
EMAIL=seanos1a@gmail.com
KEY=4551f6bda4835ee658c81221ee8783c9e7af3
ACCOUNT=fd4058c7aa1da2cb3ec2f2c9f028c022
ZONE=a0dc1c2d5a810fabb43cb596a7e4b322
TUNNEL_ID=d828b66a-192c-4230-814e-538f79006519
```
