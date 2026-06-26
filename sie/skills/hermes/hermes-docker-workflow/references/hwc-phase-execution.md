# HWC Cron Phase Execution Reference

## HWC Project Paths

| Item | Path |
|------|------|
| Workdir (source of truth) | `/opt/data/hermes-web-computer` |
| State dir | `/opt/data/hermes-web-computer-state/` |
| Phase tracker | `/opt/data/hermes-web-computer-state/PHASE_TRACKER.json` |
| Checkpoints | `/opt/data/hermes-web-computer-state/CHECKPOINTS/` |
| Feature tracker | `/opt/data/hermes-web-computer/docs/FEATURE-TRACKER.md` |
| Backend binary | `/opt/data/hermes-web-computer/backend/hwc-server` |
| Frontend dist | `/opt/data/hermes-web-computer/frontend/dist/` |

## Go Build (HWC)

The exact toolchain path `/home/hermeswebui/.hermes/home/go/.../go` does not exist in this container. Use system Go instead:

```bash
cd /opt/data/hermes-web-computer/backend
go build -o /opt/data/hermes-web-computer/backend/hwc-server ./cmd/server/
go test ./... -count=1 -timeout=120s
```

System Go: `/usr/bin/go` (go1.24.4 linux/amd64). The go.mod declares `go 1.26` but this is forward-compatible.

For the hermes-agent container's Go toolchain path (when running inside hermes container), use:
```
GOPATH=/home/hermeswebui/.hermes/home/go /home/hermeswebui/.hermes/home/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.26.0.linux-amd64/bin/go
```
Outside the container (e.g., on bare metal or in this cron environment), use system `go`.

## Frontend Build (HWC)

```bash
cd /opt/data/hermes-web-computer/frontend
/opt/data/hermes-web-computer/frontend/node_modules/.bin/vite build
```

Or via node directly (avoids vite tool resolution issues):
```bash
cd /opt/data/hermes-web-computer/frontend && node ./node_modules/.bin/vite build
```

Vite build takes ~56s. Run in background with `notify_on_complete=true`.

## Discord Notifications

The `.env` with Discord credentials is at `/opt/data/home/.hermes/.env` (inside container mount) or may not be present in this cron environment.

**This cron environment does NOT have access to the Discord bot token.** Discord notifications from this context will fail silently if the token file is missing.

To post from this environment, find the token via:
```bash
grep -E "DISCORD_BOT_TOKEN|DISCORD_CHANNEL_ID" /opt/data/home/.hermes/.env
```

## HWC Phase Structure

10 phases (0-9):
- Phase 0: Baseline verification
- Phase 1: Backend /api/system/metrics endpoint
- Phase 2: Waybar.svelte with clickable workspace dots
- Phase 3: System tray icons with real data
- Phase 4: Dock click-to-launch tiles + running indicator dot
- Phase 5: File explorer sidebar collapsible tree
- Phase 6: Bottom terminal tabs + resize handle
- Phase 7: Menu bar File/Edit/View/...
- Phase 8: XPra escape hatch
- Phase 9: Dashboard tile real data wiring

When all phases complete: POST "✅ HWC v1.3 complete — all 10 phases done. Tag: v1.3"

## Test Fix Pattern (HWC)

When adding new app types (e.g., xpra), update test assertions:
- `TestAppsList` checks `len(result.Apps)` and validates each `app.ID` against an `expected` map
- Add new app ID to both the count assertion and the expected map
