# HWC v1.3 Phase Engine — Complete

**Updated:** 2026-05-24
**Status:** ✅ All 10 phases complete. v1.3 DONE.

## Final State

| Phase | Name | Status | Commit |
|-------|------|--------|--------|
| 0 | Baseline | ✅ complete | 6c9128e |
| 1 | Backend /api/system/metrics | ✅ complete | 7566fdd |
| 2 | Waybar.svelte clickable workspace dots | ✅ complete | 8b510c6 |
| 3 | System tray icons real data | ✅ complete | 7612e58 |
| 4 | Dock click-to-launch tiles | ✅ complete | b6f85ae |
| 5 | File explorer sidebar | ✅ complete | 59f1d58 |
| 6 | Bottom terminal tabs | ✅ complete | ce60e07 |
| 7 | Menu bar | ✅ complete | 31ca7c9 |
| 8 | XPra escape hatch | ✅ complete | 0dd98fe |
| 9 | Dashboard real data wiring | ✅ complete | 2094f41 |

**Merge commit:** `fe93520` — "merge: resolve conflicts — keep xpra manager + startTime, all phases complete"

## Phase 9 Changes (Dashboard Real Data Wiring)

**Commit:** `2094f41` ("phase(9): Wire real data to dashboard tiles — system metrics, analytics, observability, overview")

**Files modified:**
- `backend/ws/multiplexer.go`: `startTime time.Time` added to Multiplexer struct
  - `system.info` → real hostname via `os.Hostname()`, OS/arch via `runtime.GOOS`/`runtime.GOARCH`, Go version via `runtime.Version()`, uptime via `time.Since(m.startTime)`
  - `system.resources` → reads `/proc/meminfo` for real host memory (previously used placeholder)
  - `system.services` → real service list with PID and uptime
  - `analytics.get` → real session counts from `m.sessions`
  - `dashboard.stats` → real session count from `m.sessions`
- `docs/FEATURE-TRACKER.md`: all features marked ✅ complete

## Key Findings This Session

1. **Workdir for HWC is `/home/hermeswebui/.hermes/hermes-web-computer`** (container path). The path `/opt/data/hermes-web-computer` does NOT exist in the container — it was wrong in the original phase engine reference. Container maps `/opt/data` from host, but the repo was moved to `/home/hermeswebui/.hermes/hermes-web-computer`. All cron jobs that reference `/opt/data/hermes-web-computer` as workdir will fail with "no such file or directory."
2. **PHASE_TRACKER.json drift**: Always cross-reference tracker with `git log --oneline` — tracker is only as accurate as the last session that updated it.
3. **HWC server runs on host, not container**: Port 3005 is on the host. Container cron jobs that try `localhost:3005` or `browser_navigate` to it will fail. Phase 14 verified server healthy on 2026-05-28, but all 3 HWC cron jobs broke after that due to container↔host boundary issues.
4. **Cron job delivery broken**: Jobs with `deliver: "local"` get rewritten to `origin` at runtime and fail with "no delivery target resolved." This is a scheduler bug (2026-06-01 evidence).
3. **Discord token path**: `/opt/data/.env` has `DISCORD_BOT_TOKEN` and `DISCORD_CHANNEL_ID`. `/home/hermeswebui/.hermes/.env` doesn't exist.
4. **All 10 phases verified in git** — no further cron job execution needed.

## Discord Notification

Manual post required (cron job would need `provider: "custom"` to work):
```python
import urllib.request, json
env = open('/opt/data/.env').read()
token = env.split('DISCORD_BOT_TOKEN=')[1].split('\n')[0]
channel = env.split('DISCORD_CHANNEL_ID=')[1].split('\n')[0]
req = urllib.request.Request(
    f'https://discord.com/api/v10/channels/{channel}/messages',
    data=json.dumps({'content': '✅ HWC v1.3 complete — all 10 phases done. Tag: v1.3'}).encode(),
    headers={'Authorization': f'Bot {token}', 'Content-Type': 'application/json'},
    method='POST')
urllib.request.urlopen(req, timeout=15)
```

## Build Verification Sequence

Per-phase verification (all must pass before commit):
```bash
# 1. Go build
cd /opt/data/hermes-web-computer/backend
GOPATH=/home/hermeswebui/.hermes/home/go \
  /home/hermeswebui/.hermes/home/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.26.0.linux-amd64/bin/go build -o /tmp/hwc-server ./cmd/server/

# 2. Go tests
cd /opt/data/hermes-web-computer/backend
GOPATH=/home/hermeswebui/.hermes/home/go \
  /home/hermeswebui/.hermes/home/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.26.0.linux-amd64/bin/go test ./... -count=1 -timeout=120s

# 3. Frontend build
cd /opt/data/hermes-web-computer/frontend
PATH="/home/hermeswebui/.hermes/home/.local/lib/python3.12/site-packages/playwright/driver:$PATH" \
  ./node_modules/.bin/vite build
```

Note: System Go (`/usr/bin/go` v1.24.4) works as fallback if toolchain path unavailable.