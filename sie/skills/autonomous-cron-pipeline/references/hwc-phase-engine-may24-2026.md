# HWC Phase Engine — May 24, 2026 (v1.3 Waybar + shell features)

## Run Summary

Phase 0 (baseline verification) completed successfully. One critical path fix applied.

## Environment Discovery

### Go Toolchain Location
- **WRONG path in PHASE_TRACKER instructions:** `/home/hermeswebui/.hermes/home/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.26.0.linux-amd64/bin/go` — does not exist
- **CORRECT path in container:** `/opt/data/home/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.26.0.linux-amd64/bin/go`
- **Also works:** system `go` at `/usr/bin/go` (go 1.24.4)
- **GOPATH:** `/opt/data/home/go`

### Repo Location
- **Container path:** `/opt/data/hermes-web-computer` (NOT `/home/hermeswebui/.hermes/hermes-web-computer`)
- PHASE_TRACKER.json has `container_workdir: "/home/hermeswebui/.hermes/hermes-web-computer"` which doesn't exist in this container
- The `workdir` field is host-side; the `container_workdir` field is wrong and stale

### State Directory
- `/opt/data/hermes-web-computer-state/` — exists, holds PHASE_TRACKER.json and CHECKPOINTS/

## Phase 0 — What Was Done

**Symptom:** `go test ./...` failed with 6 failures in `ws/` package — `fs.error: no such file or directory` for `/home/hermeswebui/.hermes/hermes-web-computer`.

**Root cause:** `filesystem.go` defaults `allowedRoot` to `/home/hermeswebui/.hermes/hermes-web-computer` which doesn't exist in the container. `HERMES_HWC_ROOT` env var was not set during test run.

**Fix:** Patch `allowedRoot` default in `filesystem.go` from `/home/hermeswebui/.hermes/hermes-web-computer` → `/opt/data/hermes-web-computer`. Also add explicit `HERMES_HWC_ROOT=/opt/data/hermes-web-computer` to test command.

**Verification:**
```bash
cd /opt/data/hermes-web-computer/backend
GOPATH=/opt/data/home/go go build -o /opt/data/hwc-server ./cmd/server/  # ✅ success
GOPATH=/opt/data/home/go HERMES_HWC_ROOT=/opt/data/hermes-web-computer go test ./... -count=1 -timeout=120s  # ✅ all pass
cd /opt/data/hermes-web-computer/frontend && npm run build  # ✅ 56s
```

**Commit:** `6c9128e` — "phase(0): fix default HERMES_HWC_ROOT path for container environment"

## Phase Tracker After Phase 0

```json
{
  "current_phase": 1,
  "phases": [
    { "id": 0, "status": "complete", "commit": "6c9128e", "checkpoint": "/opt/data/hermes-web-computer-state/CHECKPOINTS/phase-0.md" },
    { "id": 1, "status": "pending" }
  ]
}
```

## Next: Phase 1

Phase 1: Backend host metrics endpoint (`GET /api/system/metrics` → CPU%, memory%, network I/O, temperature, audio status). Wired to Waybar system tray (Phase 3).