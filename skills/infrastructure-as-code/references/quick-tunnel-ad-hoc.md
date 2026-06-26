# Cloudflare Quick Tunnel (No API Token / No cert.pem)

When you have no Cloudflare API token and no `cert.pem` (can't run `cloudflared tunnel login`), use the **quick tunnel** mode to expose a local service via `*.trycloudflare.com`.

## Prerequisites

```bash
# Download cloudflared binary (no sudo, no package manager needed)
curl -sL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
  -o /tmp/cloudflared
chmod +x /tmp/cloudflared
/tmp/cloudflared version
```

## Start a Quick Tunnel

```bash
# Expose a local port via ephemeral trycloudflare.com URL
/tmp/cloudflared tunnel --url http://localhost:PORT --no-autoupdate
```

The output shows:
```
Your quick Tunnel has been created! Visit it at (it may take some time to be reachable):
https://random-words-here.trycloudflare.com
```

**`--no-autoupdate`** prevents the binary from trying to overwrite itself in `/tmp`.

**Important:** The `--url` flag is a global flag (before `tunnel`), NOT a subcommand arg. This syntax:
```bash
/tmp/cloudflared tunnel --url http://localhost:8000    # ✅ CORRECT
/tmp/cloudflared tunnel run --url http://localhost:8000 # ❌ old syntax, may fail
```

## CLI Syntax Issues (cloudflared 2026.x)

This version has strict argument parsing. Known issues:

| Attempt | Result |
|---------|--------|
| `cloudflared --config /path tunnel run` | ✅ Works — config is a global flag |
| `cloudflared tunnel --config /path run` | ❌ `--config` treated as positional arg to `run` |
| `cloudflared tunnel run hermes-webui` | ✅ Works — tunnel name as positional |
| `cloudflared tunnel run --token TOKEN` | ✅ Works with unified tunnel token |
| `cloudflared tunnel --url http://localhost:8000` | ✅ Works — creates quick tunnel |

**Rule of thumb:** Global flags go BEFORE `tunnel`. Subcommand flags go AFTER `run` but ensure they don't collide.

## Stale Named Tunnel Credentials

When `cloudflared tunnel run` produces:
```
ERR failed to serve incoming request error="Unauthorized: Tunnel not found"
```

The tunnel credentials file (`credentials.json`) is stale — the tunnel was deleted from the Cloudflare dashboard and recreated. The credential file's `TunnelSecret` no longer matches.

**Fix options:**
1. **Recreate from dashboard** (no API token needed):
   - Go to Cloudflare Zero Trust → Tunnels → Create a tunnel
   - Copy the token/credentials file
   - Update `config.yml` with new TunnelID and credentials path
2. **Create via API** (token required):
   ```bash
   curl -s -X POST "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/tunnels" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"name":"tunnel-name","tunnel_type":"cfd_tunnel"}'
   ```
3. **Use quick tunnel** (no auth needed):
   ```bash
   /tmp/cloudflared tunnel --url http://localhost:8000
   ```

## DNS Routing for Named Tunnels

Named tunnels require a CNAME record pointing to `<tunnel-uuid>.cfargotunnel.com`. If the DNS record is an A record (pointing to server IP), the tunnel won't route traffic — Cloudflare sends traffic directly to the IP instead of through the tunnel.

```bash
# Correct DNS (CNAME):
wiz.codeovertcp.com  CNAME  →  bf723d4c-7299-4a6b-a2f9-6cee6bec86dc.cfargotunnel.com

# Wrong DNS (A record — bypasses tunnel):
wiz.codeovertcp.com  A  →  203.0.113.42
```

You can route DNS via:
```bash
cloudflared tunnel route dns tunnel-name subdomain.domain.com
```
(This requires valid `cert.pem` from `cloudflared tunnel login`.)

## Connectivity Debugging

After starting the tunnel, verify at each layer:

```bash
# Layer 1: Local service
curl -s http://localhost:8000/health

# Layer 2: Tunnel is registered (check cloudflared logs)
# Look for: "Registered tunnel connection" + "precheck complete"

# Layer 3: Cloudflare edge
curl -sv https://random-words.trycloudflare.com/health 2>&1 | grep -E "< HTTP|< cf-ray"
# cf-ray header confirms Cloudflare edge was reached

# Layer 4: Request reaches local service (check tunnel logs)
# cloudflared logs should show: "incoming request"
```

**Common failure modes:**
- Tunnel logs show only DNS/UDP/TCP pre-checks but no requests → DNS record is A record, not CNAME
- Tunnel logs show "Unauthorized: Tunnel not found" → stale credentials
- curl returns HTTP 404 but local server responds 200 → tunnel registration not propagated yet (wait 2-5 minutes) or DNS misconfigured
