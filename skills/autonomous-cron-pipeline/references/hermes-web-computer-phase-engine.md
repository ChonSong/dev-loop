# hermes-web-computer Phase Engine Reference

## Current Verified Paths (May 28, 2026)

The cron job descriptions reference paths under `/home/hermeswebui/.hermes/` but those **do not exist**. Always verify before using. Actual working paths:

| Item | Actual Path | Cron Job Stated Path (doesn't exist) |
|------|-------------|---------------------------------------|
| Repo workdir | `/opt/data/hermes-web-computer` | `/home/hermeswebui/.hermes/hermes-web-computer` |
| State dir | `/opt/data/hermes-web-computer-state/` | `/home/hermeswebui/.hermes/hermes-web-computer-state/` |
| PHASE_TRACKER | `/opt/data/hermes-web-computer-state/PHASE_TRACKER.json` | — |
| Backend binary | `/opt/data/hermes-web-computer/agent-os` | — |
| Frontend build | `cd /opt/data/hermes-web-computer && npm run build` | — |

**Discovery pattern:** When a state dir or workdir doesn't exist at the documented path, scan `/opt/data/` for `<project>` and `<project>-state/` flat directories. The project lives at `/opt/data/<project>`, not under `/home/` or `.hermes/` subdirectories.

## Go Build Command

```bash
cd /opt/data/hermes-web-computer/backend && \
  GOPATH=/home/hermeswebui/.hermes/home/go \
  /home/hermeswebui/.hermes/home/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.26.0.linux-amd64/bin/go build -o /tmp/hwc-server ./cmd/server/
```

## Run Tests

```bash
cd /opt/data/hermes-web-computer/backend && \
  GOHOME_HWC_ROOT="/opt/data/hermes-web-computer" \
  GOPATH=/home/hermeswebui/.hermes/home/go \
  /home/hermeswebui/.hermes/home/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.26.0.linux-amd64/bin/go test ./... -count=1 -timeout 60s
```

## Frontend Build

```bash
cd /opt/data/hermes-web-computer && npm run build
```

Node.js and npm are available in this environment (node_modules installed, frontend builds succeed).

## Backend Port

Port `3005` (not 3113 — that was the legacy agent-os tunnel).

## Current Phase Status (May 28, 2026)

**v1.4 complete — all phases done.** Latest tag: `v1.4` (commit `01e1781`). No pending phases.

### PHASE_TRACKER at `/opt/data/hermes-web-computer-state/PHASE_TRACKER.json`

```json
{
  "project": "hermes-web-computer",
  "version": "1.4",
  "total_phases": 14,
  "current_phase": 15,
  "status": "complete",
  "workdir": "/opt/data/hermes-web-computer",
  "last_updated": "2026-05-28T07:09:42Z"
}
```

### All Phases

| Phase | Name | Status | Commit |
|-------|------|--------|--------|
| 0 | Baseline verification | ✅ Complete | `6c9128e` |
| 1 | Backend: host metrics endpoint | ✅ Complete | `7566fdd` |
| 2 | Waybar.svelte — top bar | ✅ Complete | `8b510c6` |
| 3 | System tray icons | ✅ Complete | `7612e58` |
| 4 | Dock refinements | ✅ Complete | `b6f85ae` |
| 5 | File explorer sidebar | ✅ Complete | `59f1d58` |
| 6 | Bottom terminal panel tabs | ✅ Complete | `ce60e07` |
| 7 | Menu bar | ✅ Complete | `31ca7c9` |
| 8 | XPra escape hatch | ✅ Complete | `0dd98fe` |
| 9 | Dashboard tile real data | ✅ Complete | `62ebada` |
| 10 | Waybar + Shell features | ✅ Complete | `c6cacb9` |
| 11 | E2E test fix + validation | ✅ Complete | `d73f170` |
| 12 | E2E selector fixes | ✅ Complete | `76b81b5` |
| 13 | v1.4 release tag | ✅ Complete | `01e1781` |
| 14 | Waybar+shell verification | ✅ Complete | `01e1781` |
| 15 | v1.3 Waybar+Shell validation | ✅ Complete | `01e1781` |

## Cron Job for Phase Engine

If a cron job exists for this phase engine, its current state can be checked with `cronjob action=list`. The model/provider should be:

```yaml
model: "MiniMax-M2.7"
provider: "custom"
```

DO NOT use `provider: "minimax-portal"` — it fails with 401 in scheduler context.
