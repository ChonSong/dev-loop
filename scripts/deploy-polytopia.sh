#!/bin/bash
# Polytopia deploy watchdog — runs every 5min via no_agent cron
set -u
LOCK="/tmp/polytopia-deploy.lock"
REPO="/home/sc/repos/polytopia-clone"
SERVE_BIN="$REPO/node_modules/.bin/serve"

# Flock — exit silently if already running
exec 9>"$LOCK"
flock -n 9 || { echo "SKIP: already running"; exit 0; }

cd "$REPO" 2>/dev/null || { echo "REPO_NOT_FOUND"; exit 1; }

# ── Build ─────────────────────────────────────────────────────────────
BUILD_OUTPUT=$(npm run build 2>&1)
BUILD_OK=$(echo "$BUILD_OUTPUT" | grep -c "built in")
echo "BUILD:$BUILD_OK"

if [ "$BUILD_OK" -eq 0 ]; then
  echo "BUILD_FAILED"
  echo "$BUILD_OUTPUT" | tail -5
  exit 1
fi

# ── Unit tests ────────────────────────────────────────────────────────
TEST_OUTPUT=$(npx vitest run 2>&1)
TESTS_PASSED=$(echo "$TEST_OUTPUT" | grep -oP 'Tests\s+\d+ passed' | head -1)
echo "TESTS:${TESTS_PASSED:-0 passed}"

# ── Kill stale server ─────────────────────────────────────────────────
PIDS=$(lsof -ti:3001 2>/dev/null || true)
if [ -n "$PIDS" ]; then
  for pid in $PIDS; do
    kill "$pid" 2>/dev/null || true
  done
  sleep 1
fi

# ── Start fresh server on built dist ──────────────────────────────────
nohup "$SERVE_BIN" dist -p 3001 --cors > /tmp/polytopia-preview.log 2>&1 &
sleep 3

# Verify server is up
if ! curl -sf http://localhost:3001/ > /dev/null 2>&1; then
  echo "SERVER:FAILED"
  tail -5 /tmp/polytopia-preview.log
  exit 1
fi
echo "SERVER:OK"

# ── E2E tests ─────────────────────────────────────────────────────────
E2E_OUTPUT=$(cd "$REPO" && npx playwright test tests-e2e/ --reporter=list 2>&1)
E2E_PASSED=$(echo "$E2E_OUTPUT" | grep -c "^  ✓")
E2E_TOTAL=$(echo "$E2E_OUTPUT" | grep -c "^  [✘✓]")
echo "E2E:${E2E_PASSED:-0}/${E2E_TOTAL:-0}"

if [ "$E2E_PASSED" -lt "$E2E_TOTAL" ] || [ "$E2E_TOTAL" -eq 0 ]; then
  echo "E2E_FAILED"
  echo "$E2E_OUTPUT" | tail -10
  exit 1
fi

echo "DEPLOY_OK"
