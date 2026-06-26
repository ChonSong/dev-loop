# onetag.codeovertcp.com Tunnel Setup

## June 2026 — LIVE ✅

A new tunnel was created for `onetag.codeovertcp.com` → `http://localhost:8501` (Streamlit).

## What was done

1. **Created new tunnel** via `cfat_` API token: `POST /accounts/{id}/tunnels` → tunnel ID `b3200be4-a8a8-4381-980b-038e402d8702`
2. **Captured credentials** from create response (NOT from GET — token only returned on creation)
3. **Wrote config.yml** with ingress rules — local config WAS accepted by server for this new tunnel (no existing server-side config to override)
4. **Updated DNS CNAME**: `onetag.codeovertcp.com` → `b3200be4.cfargotunnel.com` (via `cfut_` zone token)
5. **Started tunnel** with `cloudflared tunnel --config /path/to/onetag-config.yml run`
6. **Verified**: `curl -s -o /dev/null -w "%{http_code}" https://onetag.codeovertcp.com/` → **200**

## Key insight

Local config.yml IS accepted for NEW tunnels. The server-side config override only happens when the tunnel already has a remote config. For fresh tunnels, the local config.yml ingress rules are pushed to the server on first connect.

## Two tunnels now run simultaneously on this host

| Tunnel | ID | Config | Status |
|---|---|---|---|
| `hermes-webui` | `93328a7a` | `/home/sean/.hermes/cloudflared/config.yml` | healthy |
| `onetag-tunnel-v2` | `b3200be4` | `/home/sean/.hermes/cloudflared/onetag-config.yml` | healthy |

Each has its own credentials file and config. Both started via `/home/sean/.hermes/scripts/start-tunnels.sh`.

## DNS Record

- ID: `e047a89ea069398294b17e69cda3d8d0`
- Type: CNAME
- Proxied: true
- Zone: `codeovertcp.com`

## Credentials

Stored at: `/home/sean/.cloudflared/onetag-tunnel-creds.json`