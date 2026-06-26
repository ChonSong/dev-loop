# GTO Wizard — Visual QA & Service Recovery (2026-06-10)

## Host vs Container Build Conflict

**Problem:** After starting the frontend inside the container (`npx next start -p 8564`), the live site showed the OLD pages (no `/study` route). `curl localhost:8564/study` returned 200 from inside the container but 404 from the host.

**Root cause:** The HOST had its own `next-server` process (PID 3421204) running from `/tmp/gto-wizard-clone/apps/web` — a stale build from a previous session. The container's new process at `/home/hermeswebui/gto-wizard-clone` couldn't bind to port 8564 because the host process was already listening.

**Detection:**
```bash
# Check from host perspective
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 "curl -s -o /dev/null -w '%{http_code}' http://localhost:8564/study"

# Check what process is actually on the port
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 "ss -tlnp | grep 8564"

# Check what build it's serving from
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 "ls -la /proc/<PID>/cwd"
```

**Fix:** Kill the host's stale process by PID, then start the container's fresh frontend. The host process may be in a container network namespace different from the Hermes container — use SSH to manage it directly.

## Visual QA via Host Chrome Screenshots

Since the container lacks a GUI browser, use the host's Chrome for screenshot QA:

```bash
# Take screenshot through the tunnel
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 "
google-chrome-stable --headless --disable-gpu --no-sandbox \\
  --screenshot=/tmp/gto-qa/page-name.png \\
  --window-size=1440,900 \\
  --virtual-time-budget=8000 \\
  https://wiz.codeovertcp.com/page-name
"

# Copy to container for vision_analyze
ssh ... "cat /tmp/gto-qa/page-name.png" > /tmp/page-name.png
```

Key parameters:
- `--virtual-time-budget=8000` — waits up to 8s for JS to render (essential for client-heavy pages)
- `--window-size=1440,900` — standard desktop viewport
- `--screenshot` — saves to file (full page, not viewport only)

## Playwright Config

The Playwright config at `apps/web/playwright.config.ts` must have `baseURL` matching the actual frontend port:

```typescript
use: {
  baseURL: 'http://localhost:8564',  // NOT :3000
  ...
}
```

## Service Watchdog

A bash watchdog script at `~/gto-wizard-clone/deploy-check/watchdog.sh` checks all 3 services every 5 minutes via cron (`GTO Watchdog — service health`):

1. API (port 8003) — restarts uvicorn if down
2. Frontend (port 8564) — restarts next start if down  
3. Tunnel (wiz.codeovertcp.com) — restarts cloudflared if down

The cron job is set to deliver locally and report `[SILENT]` when all services are healthy.

## Current Page Inventory

| Route | Design | Status |
|-------|--------|--------|
| `/study` | New (#0b0d0f) | Complete |
| `/equity` | New | Complete |
| `/play` | New | Complete |
| `/practice` | New | Complete |
| `/plo` | New | Complete |
| `/analyze` | New | Complete |
| `/icm` | New | Complete |
| `/courses` | New | Complete |
| `/train` | New | Complete |
| `/strategies` | New | Complete |
| `/strategy` | New | Complete |
| `/omaha` | New | Complete |
| `/bomb-pot` | New | Complete |
| `/double-board` | New | Complete |
| `/analyze/hands` | Old | Functional |
| `/analyze/leaks` | Old | Functional |
| `/analyze/viewer` | Old | Stub |
| `/spots` | Old | Functional |
| `/train/review` | Old | Functional |
