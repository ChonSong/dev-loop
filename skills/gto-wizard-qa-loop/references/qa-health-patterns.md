# GTO Wizard QA Health Patterns

Reference for interpreting health check results during QA sweeps.

## Expected Response Codes

| Endpoint | Access Method | Expected Code | Notes |
|---|---|---|---|
| `http://localhost:3000/` | Local (host) | **200** | Next.js production server (systemd user service) |
| `http://localhost:8001/api/v1/health` | Local (API direct) | JSON: status=healthy | FastAPI backend (systemd user service) |
| `https://gto.codeovertcp.com` | Public internet | **timeout** | Tunnel drops connections hourly; NOT reliable for automated QA |
| `https://wiz.codeovertcp.com` | Public internet | (verify current domain) | Deprecated — check cloudflared config.yml for active ingress rules |

## Current Architecture

- **Web:** systemd user service `gto-wizard-web.service` — Next.js 15 on port 3000
- **API:** systemd user service `gto-wizard-api.service` — FastAPI/uvicorn on port 8001
- **Tunnel:** systemd user service `gto-wizard-tunnel.service` — cloudflared
- **Infrastructure:** Docker containers for Postgres (`:5432`) and Redis (`:6379`)

No Docker bridge or gateway IP needed — services are accessible at localhost from the host.

## Public URL Instability

The HTTPS public URL frequently returns **connection timeout** (~10s). The cloudflared tunnel logs `"control stream encountered a failure"` every ~1h but self-recovers. This is a known intermittent issue. For cron-based QA sweeps, always use `localhost:3000` and `localhost:8001`.

## Service Health Check Commands

```bash
# Quick health
curl -s -o /dev/null -w "HTTP:%{http_code} TIME:%{time_total}s" http://localhost:3000/

# Check page renders
curl -s http://localhost:3000/ | grep -o '<title>[^<]*</title>'

# Check API health
curl -s http://localhost:8001/api/v1/health

# Check systemd services
systemctl --user --no-pager status gto-wizard-web.service gto-wizard-api.service gto-wizard-tunnel.service | grep -E 'Active:|●'
```

## Response Time Baseline

From localhost:
- Time to first byte: < 0.5s (Next.js local server)
- Full page load: < 2s

## Known False Alarms

- **First curl after deploy**: Next.js server may return 502 for 1-2 seconds while starting. Normal.
- **Tunnel reconnection**: cloudflared may briefly return 530 during tunnel reconnection (DNS propagation). Wait 60s and retry.
- **400 on API endpoints**: Likely frontend API URL mismatch (web calls `/api/v1/...` but backend expects `/v1/...`). Check the fetch URL in the page making the request — this is a known ongoing fix for Omaha, Bomb Pot, and Double Board variants. Not a server outage.
