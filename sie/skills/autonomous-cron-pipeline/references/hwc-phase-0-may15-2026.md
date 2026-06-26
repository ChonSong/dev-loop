# hermes-web-computer Phase Engine — May 15 2026 Session

## What Was Done

Phase 0 baseline verification:
- Fixed `allowedRoot` hardcoded path in `filesystem.go` (was `/opt/data/hermes-web-computer`, doesn't exist in container) → now `HERMES_HWC_ROOT` env var with fallback to `/home/hermeswebui/.hermes/hermes-web-computer`
- Fixed same hardcoded path in `integration_test.go` line 193
- PHASE_TRACKER.json workdir corrected from `/opt/data/hermes-web-computer` → `/home/hermeswebui/.hermes/hermes-web-computer`
- Phase 0 marked complete, current_phase advanced to 1

## Verification Results

```
Go build:   ✅ BUILD_OK
Backend:    ✅ HTTP 200 on port 3113
Unit tests: ✅ ok hermes-web-computer/backend/ws 1.067s
Commit:     7da6b5f "fix: make allowedRoot configurable via HERMES_HWC_ROOT env var"
```

## Environment Findings

| Component | Status | Notes |
|-----------|--------|-------|
| Go binary | ✅ Available | `/home/hermeswebui/.hermes/home/go/.../toolchain@v0.0.1-go1.26.0.linux-amd64/bin/go` |
| Node.js | ❌ NOT available | No `node` or `npm` in container |
| Docker | ❌ NOT available | No `/var/run/docker.sock` |
| SSH to host | ❌ Port 22 refused | openssh-server not installed on host |
| Backend server | ✅ Running | Port 3113 |
| Frontend | ❌ Blocked | Can't start without Node.js |

## Go Build/Test Commands (non-standard Go path)

```bash
# Build
cd /home/hermeswebui/.hermes/hermes-web-computer/backend && \
GOPATH=/home/hermeswebui/.hermes/home/go \
  /home/hermeswebui/.hermes/home/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.26.0.linux-amd64/bin/go \
  build -o /tmp/hwc-server ./cmd/server/

# Test (with HERMES_HWC_ROOT)
HERMES_HWC_ROOT="/home/hermeswebui/.hermes/hermes-web-computer" \
GOPATH=/home/hermeswebui/.hermes/home/go \
  /home/hermeswebui/.hermes/home/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.26.0.linux-amd64/bin/go \
  test ./ws/... -count=1 -timeout 60s
```

## Cron Job Created

- **Job ID:** `f5a499e5d25a`
- **Schedule:** every 60m, repeat 3
- **Model:** minimax-m2.7 via minimax-portal
- **Deliver:** discord
- **Next run:** 2026-05-15T11:40:27+00:00

## Next Pending Phase

**apps-protocol** (Phase 1): apps.list and apps.launch fully wired
- apps.list should return registered app types (terminal, editor, browser, dashboard)
- apps.launch should create PTY or editor tile and return tile_id

## Files Changed

```
backend/ws/filesystem.go        — added getAllowedRoot() with HERMES_HWC_ROOT env var
backend/ws/integration_test.go   — use HERMES_HWC_ROOT env var instead of hardcoded path
project-state/hermes-web-computer/PHASE_TRACKER.json  — workdir + phase0 status
project-state/hermes-web-computer/CHECKPOINTS/phase-0-complete.md  — checkpoint
```