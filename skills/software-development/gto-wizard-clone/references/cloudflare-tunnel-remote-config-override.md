# Cloudflare Tunnel Remote Config Override

**Problem:** Named Cloudflare tunnels have a REMOTE configuration that overrides the local `--config` YAML file. Even if `gto-wizard.yml` has `service: http://172.19.0.2:8555`, the Cloudflare dashboard pushes `service: http://localhost:8555` (the old address).

**Tunnel log evidence:**
```
INF Updated to new configuration config="{\"ingress\":[{\"service\":\"http://localhost:8555\"}]}" version=1
ERR Unable to reach origin ... dial tcp [::1]:8555: connect: connection refused
```

**Fix: Update remote config via Cloudflare API:**
```python
import json, urllib.request

CF_EMAIL = "seanos1a@gmail.com"
CF_KEY = "4551f6bda4835ee658c81221ee8783c9e7af3"
TUNNEL_ID = "24362d8c-acda-43ca-87d7-9f422b631b11"
ACCOUNT_ID = "fd4058c7aa1da2cb3ec2f2c9f028c022"

url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/cfd_tunnel/{TUNNEL_ID}/configurations"
headers = {"X-Auth-Email": CF_EMAIL, "X-Auth-Key": CF_KEY, "Content-Type": "application/json"}
body = {
    "config": {
        "ingress": [
            {"hostname": "wiz.codeovertcp.com", "service": "http://172.19.0.2:PORT"},
            {"service": "http_status:404"}
        ],
        "warp-routing": {"enabled": False}
    }
}

req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers, method="PUT")
resp = urllib.request.urlopen(req)
```

The tunnel picks up config changes within ~30 seconds without restart. No need to kill/restart cloudflared.

**Local config file** (`/home/sean/.cloudflared/gto-wizard.yml` on host):
```yaml
tunnel: gto-wizard
credentials-file: /home/sean/.cloudflared/gto-wizard.json
ingress:
  - hostname: wiz.codeovertcp.com
    service: http://172.19.0.2:PORT
  - service: http_status:404
```

**Important:** The local YAML is the INTENDED config. The remote config overrides it silently. Always update BOTH the YAML AND the API remote config when changing ports.
