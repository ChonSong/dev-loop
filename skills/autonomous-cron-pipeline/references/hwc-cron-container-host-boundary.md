# HWC Cron Jobs — Container vs Host Boundary

**Created:** 2026-06-01
**Status:** Active reference for diagnosing HWC cron job failures

## Problem

All 3 HWC cron jobs error on every run because the cron jobs execute inside the Docker container but the hermes-web-computer server and build tools are on the host.

## The Three Jobs

| Job ID | Name | Schedule | Error |
|--------|------|----------|-------|
| `4d2609ce31ba` | canary watch | 14,18,22 UTC | `browser_navigate` to `localhost:3005` — container can't reach host localhost |
| `ecb3846b907b` | rebuild + deploy | 16,20 UTC | `workdir: /opt/data/hermes-web-computer` doesn't exist in container |
| `4285b8696203` | nightly build health | 19:00 UTC | SSH to `172.19.0.1` fails from container |

## Repo Location

- **Container path:** `/home/hermeswebui/.hermes/hermes-web-computer` (Go source here, node_modules here)
- **Host path (historical):** `/opt/data/hermes-web-computer` (used by Phase Engine, may not exist in container)
- **Server process:** Runs on HOST, port 3005, binary at `/opt/data/hermes-web-computer-state/hwc-server`

## Build Tools

- **Go:** NOT installed in container. Use vendored path:
  ```
  GOPATH=/home/hermeswebui/.hermes/home/go /home/hermeswebui/.hermes/home/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.26.0.linux-amd64/bin/go
  ```
- **Node/npm:** Installed in container at `/home/hermeswebui/.hermes/hermes-web-computer/node_modules`
- **SSH:** Key at `/tmp/container_key`; SSH to host often fails from container

## Server Health

As of Phase 14 (2026-05-28): server was healthy, Go tests passed (5/5), E2E 24/24, frontend built clean. No evidence the server is down — the cron jobs just can't reach it.

## Fix Strategy

**Option A — Fix each job:**
1. Canary: Change to SSH-based check (`ssh sean@localhost "curl -s http://localhost:3005"`) — requires working SSH
2. Rebuild: Change workdir to `/home/hermeswebui/.hermes/hermes-web-computer`; use vendored Go path
3. Nightly: Run Go tests in-container (repo is there), skip host SSH

**Option B — Save host-based checks for on-demand:**
These 3 jobs fire every 4 hours and produce errors every time. Unless the server is expected to flap, they're noise. Consider disabling and running manual checks when needed.

**Option C — Accept noise:**
If the server is stable (Phase 14 confirmed), these jobs are cosmetic. Leave them erroring until there's a real issue, then SSH to host to diagnose.

## Diagnosis Checklist

When HWC cron jobs show `last_status: "error"`:
1. Check `last_delivery_error` — if "no delivery target resolved", it's the deliver bug (cosmetic)
2. If job actually ran but tests failed: check whether it used the right workdir and Go path
3. If canary can't reach port 3005: server may have died, check on host with `curl localhost:3005`
4. The project state is in git at `/home/hermeswebui/.hermes/hermes-web-computer` — always check there, not `/opt/data/`
