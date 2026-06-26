# GTO Wizard Tunnel — Live Reference (Updated June 9, 2026)

## Current State (Verified Live)

| Field | Value |
|---|---|
| **Active tunnel** | `gto-wizard` |
| **Tunnel ID** | `24362d8c-acda-43ca-87d7-9f422b631b11` |
| **Connections** | 4 healthy (status: `healthy`) |
| **Public URL** | `https://wiz.codeovertcp.com` |
| **Origin** | `http://localhost:8564` (tunnel runs IN container, uses localhost) |
| **DNS CNAME** | `24362d8c-acda-43ca-87d7-9f422b631b11.cfargotunnel.com` (proxied) |
| **Config file** | `/home/hermeswebui/.cloudflared/gto-wizard-real-config.yml` |
| **Credentials** | `/home/hermeswebui/.cloudflared/gto-wizard-original-creds.json` |
| **API auth** | Global API key via `X-Auth-Email` + `X-Auth-Key` (NOT Bearer) |
| **Zone ID** | `a0dc1c2d5a810fabb43cb596a7e4b322` |
| **Account ID** | `fd4058c7aa1da2cb3ec2f2c9f028c022` |
| **API Key** | `4551f6bda4835ee658c81221ee8783c9e7af3` |

## Services

| Port | Service | Status |
|------|---------|--------|
| 8564 | Next.js GTO Wizard (production start) | `next start -p 8564` — CORRECT codebase |
| 8003 | FastAPI backend | `uvicorn main:app --port 8003` — 96 API routes |
| 8002 | _(dead)_ | Old API port, rewrites updated to 8003 |

## API Proxying

API is proxied through Next.js rewrites, NOT through tunnel ingress path rules.
The tunnel has a single ingress rule pointing to the frontend. `next.config.ts` rewrites `/api/:path*` etc. to `http://localhost:8003`.

This is more reliable than path-based tunnel ingress which returned 500 for all API requests.

## Startup Sequence

```bash
# 1. API
export PATH="/home/hermeswebui/.hermes/home/.local/bin:$PATH"
cd /home/hermeswebui/gto-wizard-clone
PYTHONPATH="apps/api:packages/poker-core/src" uvicorn main:app --host 0.0.0.0 --port 8003 --log-level warning

# 2. Frontend (rebuild after next.config.ts changes)
export PATH="/home/hermeswebui/.hermes/node/bin:$HOME/.local/bin:$PATH"
export NEXT_PUBLIC_API_URL=http://localhost:8003
cd /home/hermeswebui/gto-wizard-clone/apps/web
npx next build
npx next start -p 8564

# 3. Tunnel
export PATH="/home/hermeswebui/.hermes/bin:$PATH"
cloudflared tunnel --config /home/hermeswebui/.cloudflared/gto-wizard-real-config.yml run

# 4. Verify
curl -sL http://localhost:8564/ | grep '<title>'
curl -s http://localhost:8003/api/v1/health
curl -s http://localhost:8564/api/v1/health   # via rewrite
```

## Troubleshooting

### Stale Frontend Process
**Symptom:** `npx next start -p 8564` fails with EADDRINUSE.
**Fix:** `find /proc -name cmdline | xargs grep -l 8564` then `kill -9` each parent PID.

### API 500 Through Tunnel
**Symptom:** API works locally but returns 500 via tunnel.
**Fix:** Kill old frontend, rebuild with correct NEXT_PUBLIC_API_URL, remove /api/* ingress from tunnel config.

## Tunnel Credential Files on Disk

| File | Tunnel ID | Status |
|------|-----------|--------|
| `gto-wizard-creds.json` | `d828b66a-192c-4230-814e-538f79006519` | ORPHAN |
| `gto-wizard-original-creds.json` | `24362d8c-acda-43ca-87d7-9f422b631b11` | ACTIVE |
| `gto-wizard-v2-creds.json` | `92674c6b-d706-4639-a403-89706fe5782b` | OBSOLETE |

## Config Files

| File | Tunnel ID | Use |
|------|-----------|-----|
| `gto-wizard-real-config.yml` | `24362d8c` | ACTIVE — tunnel ingress |
| `gto-wizard-config.yml` | `d828b66a` | Old — orphan |
| `gto-wizard-original-config.yml` | `24362d8c` | Also works |
| `gto-wizard-v2-config.yml` | `92674c6b` | Obsolete |

Active config:
```yaml
tunnel: 24362d8c-acda-43ca-87d7-9f422b631b11
credentials-file: /home/hermeswebui/.cloudflared/gto-wizard-original-creds.json
no-autoupdate: true
ingress:
  - hostname: wiz.codeovertcp.com
    service: http://localhost:8564
  - service: http_status:404
```

## Orphan Tunnel History

| Date | Credential Created | Notes |
|------|-------------------|-------|
| June 7 | `d828b66a` | Created by API, never used. Orphan. |
| June 6 | `92674c6b` (v2) | Created earlier, stale. |
| Pre-June 6 | `24362d8c` (original) | ACTIVE. DNS points here. |

## 530 Error Diagnostics

**Problem:** Tunnel healthy but HTTP 530.
**Root cause:** Three things MUST match: DNS CNAME tunnel ID, credentials file tunnel ID, API-registered tunnel ID. If any two point to different IDs → 530.
**Fix:** Kill orphan processes, update DNS CNAME to match active tunnel credentials, update API ingress config, restart cloudflared.

## Key Lesson

**Three things MUST match for a tunnel to work:**
1. DNS CNAME target tunnel ID
2. Credentials file tunnel ID (what cloudflared connects as)
3. Cloudflare API registered tunnel ID (what the API says exists)

If any two point to different tunnel IDs, you'll get 530 even though everything looks healthy.
