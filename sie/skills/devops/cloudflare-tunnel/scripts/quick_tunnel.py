#!/usr/bin/env python3
"""Quick Cloudflare Tunnel setup — creates tunnel, config, DNS, and credentials in one shot.

Usage:
  python3 quick_tunnel.py --domain example.com --subdomain app --port 8080 --token CF_API_TOKEN
"""
import argparse, json, os, base64, sys
from urllib.request import Request, urlopen

def api(method, url, token, data=None):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    body = json.dumps(data).encode() if data else None
    req = Request(url, data=body, headers=headers, method=method)
    with urlopen(req) as resp:
        return json.loads(resp.read())

def main():
    p = argparse.ArgumentParser(description="Create Cloudflare Tunnel + DNS in one shot")
    p.add_argument("--domain", required=True, help="Domain (e.g. example.com)")
    p.add_argument("--subdomain", required=True, help="Subdomain (e.g. app -> app.example.com)")
    p.add_argument("--port", required=True, help="Local port (e.g. 8080)")
    p.add_argument("--token", required=True, help="Cloudflare API token")
    p.add_argument("--name", default=None, help="Tunnel name (default: auto)")
    args = p.parse_args()

    BASE = "https://api.cloudflare.com/client/v4"
    name = args.name or f"{args.subdomain}-{args.domain.replace('.','-')}"

    # 1. Get account & zone
    print("[1/6] Getting account...")
    accts = api("GET", f"{BASE}/accounts", args.token)
    acct_id = accts["result"][0]["id"]

    print("[2/6] Getting zone...")
    zones = api("GET", f"{BASE}/zones?name={args.domain}", args.token)
    zone_id = zones["result"][0]["id"]

    # 2. Generate secret & create tunnel
    print("[3/6] Creating tunnel...")
    secret = base64.b64encode(os.urandom(32)).decode()
    tun = api("POST", f"{BASE}/accounts/{acct_id}/cfd_tunnel", args.token, {
        "name": name, "tunnel_secret": secret
    })
    if not tun.get("success"):
        print(f"ERROR: {tun.get('errors')}"); sys.exit(1)
    tun_id = tun["result"]["id"]
    print(f"  Tunnel: {name} ({tun_id})")

    # 3. Configure ingress
    print("[4/6] Configuring ingress...")
    api("PUT", f"{BASE}/accounts/{acct_id}/cfd_tunnel/{tun_id}/configurations", args.token, {
        "config": {
            "ingress": [
                {"hostname": f"{args.subdomain}.{args.domain}", "service": f"http://localhost:{args.port}"},
                {"service": "http_status:404"}
            ],
            "warp-routing": {},
            "__configuration_flags": {"no-autoupdate": "true"}
        }
    })

    # 4. Create DNS
    print("[5/6] Creating DNS CNAME...")
    fqdn = f"{args.subdomain}.{args.domain}"
    api("POST", f"{BASE}/zones/{zone_id}/dns_records", args.token, {
        "type": "CNAME", "name": args.subdomain,
        "content": f"{tun_id}.cfargotunnel.com",
        "ttl": 1, "proxied": True
    })
    print(f"  DNS: {fqdn} CNAME -> {tun_id}.cfargotunnel.com")

    # 5. Save credentials
    print("[6/6] Saving credentials...")
    creds = {"AccountTag": acct_id, "TunnelID": tun_id, "TunnelName": name, "TunnelSecret": secret}
    creds_path = os.path.expanduser(f"~/.cloudflared/{name}-creds.json")
    os.makedirs(os.path.dirname(creds_path), exist_ok=True)
    with open(creds_path, "w") as f:
        json.dump(creds, f, indent=4)

    config_str = f"""tunnel: {tun_id}
credentials-file: {creds_path}
no-autoupdate: true
ingress:
  - hostname: {fqdn}
    service: http://localhost:{args.port}
  - service: http_status:404
"""
    config_path = os.path.expanduser(f"~/.cloudflared/{name}-config.yml")
    with open(config_path, "w") as f:
        f.write(config_str)

    print(f"\n✅ Done! Run: cloudflared --config {config_path} tunnel run {tun_id}")
    print(f"   Tunnel: localhost:{args.port} -> https://{fqdn}")

if __name__ == "__main__":
    main()
