# hermes-web-computer Phase Engine — May 15 2026 Complete Run

**Status: ALL 9 PHASES COMPLETE — v1.2 TAGGED**

## Verified Paths

| Item | Value |
|------|-------|
| Repo | `/home/hermeswebui/.hermes/hermes-web-computer` |
| State dir | `/home/hermeswebui/.hermes/project-state/hermes-web-computer/` |
| Go binary | `/home/hermeswebui/.hermes/home/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.26.0.linux-amd64/bin/go` |
| Build cmd | `GOPATH=/home/hermeswebui/.hermes/home/go /path/to/go build -o /tmp/hwc-server ./cmd/server/` |
| Test cmd | `GOPATH=/home/hermeswebui/.hermes/home/go /path/to/go test ./... -count=1 -timeout 60s` |
| Env var for allowedRoot | `HERMES_HWC_ROOT=/home/hermeswebui/.hermes/hermes-web-computer` |

**Old path `/opt/data/hermes-web-computer` does not exist — do not use.**

## Complete Phase Log

| Phase | Commit | Description |
|-------|--------|-------------|
| phase0 | `6e12f52` | Testing infra baseline (Go build, allowedRoot fix, ws tests pass) |
| tool-execute | `a6d29f4` | Hermes Agent API wired via tool.execute |
| apps-protocol | `7da6b5f` | apps.list + apps.launch fully wired |
| voice-bridge | `ee0120a` | Fun-Audio-Chat audio relay in backend/audio/bridge.go |
| layout-engine-tests | `0a8b074` | 24 unit tests in backend/layout/tree_test.go |
| github-actions | `13aa8f1` | CI workflow (lint→e2e→a11y→visual→nightly) |
| precommit-hooks | `bfa73af` | Husky pre-commit + prepare script |
| bundle-optimization | `a34b07c` | Monaco code-split, DashAnalytics/DashObservability lazy-load |
| final-polish | `50b14d9` | v1.2 tagged, PHASE_TRACKER status=complete |

## Key Fixes Applied During Phase 0

1. **`allowedRoot` hardcoded path** — `backend/ws/filesystem.go:14` had `"/opt/data/hermes-web-computer"` (doesn't exist). Fixed to use `getAllowedRoot()` reading from `HERMES_HWC_ROOT` env var.
2. **Test hardcoded path** — `backend/ws/integration_test.go:193` referenced wrong path. Fixed to use `os.Getenv("HERMES_HWC_ROOT")`.
3. **PHASE_TRACKER.json workdir** — Had wrong path. Corrected to `/home/hermeswebui/.hermes/hermes-web-computer`.

## Scheduler Issue

`cronjob action=run` is broken — returns 404 on all job trigger endpoints. The scheduler process runs on port 8787 but the job trigger API doesn't exist in this version.

**Execution pattern that works:**
- `delegate_task` — immediate execution, results visible in current session
- Cron job timer (`every 60m`) — fires on schedule, results via `deliver: origin`
- Cron job `run` via scheduler — broken (404), do not use

All 9 phases were completed via `delegate_task` when the scheduler `run` was unavailable. The phase engine is tracker-based and works with either execution mechanism.

## Cron Jobs

| Job ID | Name | Status |
|--------|------|--------|
| `85d63c9f073a` | HWC Phase Engine (60m) | Paused — all phases complete |
| (others) | Various cron jobs | `provider: minimax-portal` → batch-fixed to `custom` |

All jobs with `provider: minimax-portal` caused 401 auth failures. Batch-fixed by setting `model={"model": "MiniMax-M2.7"}` (omits provider → uses `custom`).

## v1.2 Tag

```
git tag -a v1.2 -m "feat: phase engine complete — voice bridge, layout tests, CI, pre-commit, bundle opt"
git push origin v1.2
```

Pushed to `origin/main`.