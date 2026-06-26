# Phase Engine — Container Environment Reference

## What This Is

The hermes-web-computer v1.4 phase engine runs as a cron job in this container. It reads `PHASE_TRACKER.json` and executes the next pending phase on each run.

**v1.4 is complete (2026-05-25).** All phases 0-5 of the v1.4 plan (`plans/hwc-v1.4-replace-hermes-webui.md`) are done. Phase 6 (observability expansion: trace view, cost ledger, skills analytics) and Phase 7 (multi-user / OIDC auth) are pending but marked "later" in the plan.

## Critical Path Correction (2026-05-25)

> ⚠️ **State dir path mismatch:** The cron job instruction said `/home/hermeswebui/.hermes/hermes-web-computer-state/` — this path is **inaccessible** from this container (permission denied, user is `hermes` not `hermeswebui`).
>
> **Use `/opt/data/hermes-web-computer-state/` as the state dir.** The working copy is at `/opt/data/hermes-web-computer/` (also symlinked as `/opt/data/cache/hermes-web-computer/hermes-web-sync/opt/data/hermes-web-computer`). All checkpoints live at `/opt/data/hermes-web-computer/CHECKPOINTS/`.
>
> Always check which path is actually accessible before writing checkpoints.

## Directory Structure

```
/opt/data/hermes-web-computer/                    ← WORKDIR (source of truth, git push target)
/opt/data/hermes-web-computer-state/              ← STATE_DIR
├── PHASE_TRACKER.json
└── CHECKPOINTS/
    ├── phase-0.md … phase-10.md
    └── phase-10-complete.md

# Cache/sync copies (alternate path, not working target)
/opt/data/cache/hermes-web-computer/hermes-web-sync/hermes-web-computer-state/
```

On the EndeavourOS host, the equivalent is `/home/sean/.hermes/hermes-web-computer/`.

## Phase Tracker Shape

The `PHASE_TRACKER.json` has two formats:

**v1.3 format** (what's currently there — 10 phases):
```json
{
  "current_phase": 10,
  "phases": [
    { "id": 0, "status": "complete", "commit": "6c9128e", "checkpoint": "..." },
    ...
    { "id": 9, "status": "complete", "commit": "2094f41", "checkpoint": "..." }
  ]
}
```

After completing a phase: update `phases[N].status="complete"`, `phases[N].commit=<hash>`, `phases[N].checkpoint=<path>`, and `current_phase=N+1`.

## v1.4 Plan — All Phases Summary

| Phase | Steps | Status | Key Commits |
|-------|-------|--------|-------------|
| 0 | WS connection fix (:3113→:3005), manager bootstrap | ✅ done | `55fed3f` |
| 1 | DockerPanel + session/security path migration | ✅ done | `96288c4`, `59aa98c` |
| 2 | FileTree wired, slash commands, file upload, session search, context meter | ✅ done | `a35d1e6`–`b6eac64` |
| 3 | Docker CRUD, images tab, compose projects | ✅ done | `c6cacb9` |
| 4 | Research cards, connection status reconnect, message search, session projects | ✅ done | `0a01317`, `039f8cd` |
| 5 | Xpra escape hatch | ✅ done | `01c1fec` |
| 6 | Trace view, cost ledger, skills analytics | ⬜ later | — |
| 7 | OIDC auth, per-user session isolation, Coder workspace lifecycle | ⬜ later | — |

## Container Go Toolchain

Both the go1.26.0 toolchain at `/opt/data/home/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.26.0.linux-amd64/bin/go` AND the system go at `/usr/bin/go` (1.24.4) are available. Go's forward compatibility treats `go 1.26` in `go.mod` as a minimum, not an exact requirement.

```bash
# All go commands need GOPATH set
GOPATH=/opt/data/home/go go build -o /opt/data/hwc-server ./cmd/server/

# For tests (MUST set HERMES_HWC_ROOT)
GOPATH=/opt/data/home/go HERMES_HWC_ROOT=/opt/data/hermes-web-computer go test ./... -count=1 -timeout=120s
```

## HERMES_HWC_ROOT for Tests

`filesystem_test.go` and `integration_test.go` in `ws/` use `HERMES_HWC_ROOT` to find the repo root. Without it, tests look for `/home/hermeswebui/.hermes/hermes-web-computer` (non-existent in container) and fail with `fs.error: no such file or directory`.

```bash
# Correct
GOPATH=/opt/data/home/go HERMES_HWC_ROOT=/opt/data/hermes-web-computer go test ./...

# WRONG — will fail
GOPATH=/opt/data/home/go go test ./...
```

## Phase Completion Checklist

1. `go build -o /opt/data/hwc-server ./cmd/server/` → success
2. `GOPATH=/opt/data/home/go HERMES_HWC_ROOT=/opt/data/hermes-web-computer go test ./... -count=1 -timeout=120s` → all pass
3. `cd /opt/data/hermes-web-computer/frontend && npm run build` → success
4. `git add . && git commit -m "phase(N): <desc>"`
5. `git push`
6. Write checkpoint: `/opt/data/hermes-web-computer/CHECKPOINTS/phase-N.md`
7. Update `PHASE_TRACKER.json`: phase status + commit hash + checkpoint path
8. Push tracker update (separate commit or same, either works)

## Finding the Next Pending Phase

```python
import json
with open('/opt/data/hermes-web-computer-state/PHASE_TRACKER.json') as f:
    tracker = json.load(f)
for p in tracker['phases']:
    if p['status'] == 'pending':
        print(f"Phase {p['id']}: {p['name']}")
        break
```

If all phases show "complete", check `plans/hwc-v1.4-replace-hermes-webui.md` header — v1.4 may have its own phase list with different statuses (the plan's Step statuses were all "pending" but the actual commits are all done).