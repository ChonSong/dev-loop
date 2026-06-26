# No-Agent Script Timeout — Case Study

## Job: Polytopia Deploy Loop

**Job ID:** `752d51adb96d`
**Date:** 2026-06-16
**Schedule:** Every 5 minutes
**Script:** `/home/sc/.hermes/scripts/deploy-polytopia.sh`
**Mode:** `no_agent: true`

## Symptoms

- `hermes cron list` showed: `error: Script timed out after 120s`
- Output files showed the same error every 5 minutes — **10+ consecutive failures in ~1 hour**
- All other cron jobs (15) were healthy
- Gateway and scheduler were running normally

## Diagnosis

### Step 1: Read the output files

```
ls /home/sc/.hermes/cron/output/752d51adb96d/
```
20 files from today alone, all showing the same timeout error. Rapid-interval failures accumulate fast — file count is the best proxy for "how many consecutive".

### Step 2: Check if the build was making progress

```
ls -la /home/sc/repos/polytopia-clone/dist/
```
`dist/` existed with a timestamp updated just before the timeout — **the build phase WAS completing**. The bottleneck was post-build (tests or server start).

### Step 3: Check port occupancy

```
ss -tlnp | grep 3001
```
Port 3001 was in use by a separate `node` process (PID 890618). The script tries to `kill $(lsof -ti:3001)` and restart via `npx serve dist -p 3001` — but the combined build+test+kill+serve chain exceeds 120s.

### Step 4: Check for hanging processes

```
ps aux | grep -E 'npm|vite|vitest|tsc'
```
No stale vite/tsc processes found. The bottleneck is likely `npx vitest run` taking too long, or the server restart logic.

## Resolution Path

The `deploy-polytopia.sh` script chains:
1. `npm run build` (= `tsc && vite build`) — succeeds but takes significant time
2. `npx vitest run` — test runner, may be slow
3. Kill old server on port 3001 + `npx serve dist -p 3001` — server restart

## Applied Fix (2026-06-17)

The script was updated with two targeted changes:

### Fix 1: Use local serve binary, not `npx serve`

**Before:** `nohup npx serve dist -p 3001 --cors > /tmp/polytopia-preview.log 2>&1 &`
**After:** `nohup "$REPO/node_modules/.bin/serve" dist -p 3001 --cors > /tmp/polytopia-preview.log 2>&1 &`

`npx serve` can hang indefinitely when cron's environment lacks npm registry connectivity or when npx performs version checks before running the binary. Using the local `node_modules/.bin/serve` directly eliminates the network dependency — the binary is already installed and never needs to check for updates.

**How to check if this is the bottleneck:** run the script with a minimal cron-like env:
```bash
env -i HOME="$HOME" PATH="/usr/bin:/bin" timeout 30 bash deploy-polytopia.sh
```
If it completes in <30s, the cron failure was npx-related. If it still times out, the bottleneck is elsewhere.

### Fix 2: Guard lsof output against empty PID list under `set -e`

**Before:** `for pid in $(lsof -ti:3001 2>/dev/null); do kill "$pid"; done`
**After:**
```bash
PIDS=$(lsof -ti:3001 2>/dev/null || true)
if [ -n "$PIDS" ]; then
  for pid in $PIDS; do
    kill "$pid" 2>/dev/null && echo "KILLED_PID:$pid"
  done
fi
```

With `set -e` active, `kill ""` (when `lsof` returns no PIDs and the for loop produces an empty string) exits the entire script. The fix captures PIDs into a variable first, guards with `-n`, and uses `|| true` to tolerate `lsof` failures.

### Verification

After the fix, the script completed in ~10s:
```
BUILD:1
TESTS:Tests  228 passed
KILLED_PID:...
SERVER:RESTARTING
SERVER:RESTARTED_OK
DEPLOY_OK
EXIT:0
```

No further timeouts in subsequent cron ticks.

## Other Fix Options Considered

1. **Increase the 120s timeout** — doesn't fix the root cause (npx hang), just masks it
2. **Split build-check and deploy into separate cron jobs** — viable for larger projects, but unnecessary once npx hang is eliminated

## Key Takeaways

1. **Rapid-interval job failures compound fast** — 10+ failures in 1 hour for a 5-minute job. Use output directory file count, not `last_run_at`, to gauge severity.
2. **`dist/` timestamps tell you the build succeeded** — even when the overall script times out, partial progress markers are invaluable.
3. **Port in use ≠ healthy** — a server process on the target port may be orphaned from a prior run, and the script's kill+restart logic adds latency.
4. **Chained build+test+deploy scripts are the most likely no-agent timeout candidates** — each phase adds cumulative time, and the default 120s can be tight.
