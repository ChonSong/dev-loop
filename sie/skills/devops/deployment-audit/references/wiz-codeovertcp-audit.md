# wiz.codeovertcp.com — Deployment Audit Reference

State as of June 9, 2026 (second session). Use as a worked example for `deployment-audit` skill.

## Target
- URL: https://wiz.codeovertcp.com
- Intended codebase: `ChonSong/gto-wizard-clone` at `/home/hermeswebui/gto-wizard-clone`
- Intended frontend: 8564 (Next.js 15 production, title "GTO Wizard")
- Intended API: 8003 (FastAPI/uvicorn, 96 routes)

## What Was Actually Found (June 8 — Initial Audit)

- Port 8564 serving **open-lovable** (title "Open Lovable v3") instead of gto-wizard-clone
- API port 8003: nothing listening
- Tunnel config pointing to Docker bridge IP, no API route
- Dual-Base DB issue: seeded data invisible to API

## What Happened When We Tried to Fix It (June 9)

### Step 1: Kill Wrong Server
Killed `open-lovable` dev process on port 8564.
✅ Port freed.

### Step 2: Start Correct Frontend
```bash
export PATH="/home/hermeswebui/.hermes/node/bin:$PATH"
cd /home/hermeswebui/gto-wizard-clone/apps/web
npx next start -p 8564
```
⚠️ First attempt started successfully but was running the OLD next.config.ts (rewrites to port 8002).

### Step 3: Start API
```bash
cd /home/hermeswebui/gto-wizard-clone
PYTHONPATH="apps/api:packages/poker-core/src" uvicorn main:app --host 0.0.0.0 --port 8003
```
✅ 96 API routes. `/api/v1/health` returns 200.

### Step 4: Fix next.config.ts
Updated all rewrites from port 8002 → 8003. Rebuilt frontend.

### Step 5: Tunnel Config
Two approaches tried:
1. **Path-based ingress** (tunnel config with `/api/*:localhost:8003`) → **FAILED** — all API requests returned 500 through tunnel despite working locally
2. **Next.js rewrites only** (tunnel routes everything to frontend at :8564) → **WORKED** — frontend returns 200

### Step 6: Port Conflict
After killing the old frontend with `pkill -9 -f "next start"`, a new `next start` attempt failed with `EADDRINUSE`. The old process tree (bash → npm → sh → next) resisted `kill -9`.
🔴 **Unresolved at end of session** — site shows correct codebase title but API calls through tunnel return 500 because the OLD build is still running on port 8564.

## Root Causes Found

### API 500 Through Tunnel
**Cause:** The running frontend had the OLD build (rewrites to port 8002, dead). Rebuilding with corrected `next.config.ts` doesn't help if the NEW frontend process can't start because the old one holds the port.

**Fix sequence that will work:**
1. Kill ALL processes on port 8564 (find each PID in the process tree, kill parent first)
2. Start rebuilt frontend with `NEXT_PUBLIC_API_URL=http://localhost:8003`
3. Before declaring success: `curl http://localhost:8564/api/v1/health` must return JSON 200
4. Verify title: `curl -sL http://localhost:8564/ | grep '<title>'` → "GTO Wizard"

## Key Lessons for Future Audits

### Lesson 1: Title Check is Mandatory but Not Sufficient
The title check caught the wrong codebase (June 8) but didn't catch the stale-build-on-correct-codebase issue (June 9). Combine title check + API-health-through-rewrite check.

### Lesson 2: "Running" is Not the Same as "Deployed Correctly"
A process on the right port serving the right codebase can still serve the wrong BUILD if the config/env changed between builds.

### Lesson 3: Process Cleanup Needs Tree Killing
```bash
# This doesn't work for bash-wrapper processes:
pkill -9 -f "next.*8564"  # misses parent bash processes

# This works — find and kill every PID:
find /proc -maxdepth 2 -name "cmdline" | xargs grep -l "8564" | while read f; do
  pid=$(echo $f | cut -d/ -f3)
  kill -9 $pid 2>/dev/null || true
done
sleep 2
```

### Lesson 4: Next.js Rewrites > Tunnel API Ingress
Path-based tunnel ingress for `/api/*` with same-hostname rules returns 500. Frontend rewrites are more reliable for Next.js + FastAPI monorepos.

## Fix Sequence — Corrected

1. `kill -9` every process on port 8564 (find via `find /proc`)
2. Kill any uvicorn on port 8003, restart fresh
3. Build: `export NEXT_PUBLIC_API_URL=http://localhost:8003 && npx next build`
4. Start API: `uvicorn main:app --host 0.0.0.0 --port 8003`
5. Start frontend: `npx next start -p 8564`
6. Verify title + API rewrite + health
7. Start tunnel: `cloudflared tunnel --config <config> run`
8. Verify public URL returns correct title + API works end-to-end
