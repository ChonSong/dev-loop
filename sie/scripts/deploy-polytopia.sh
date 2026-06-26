#!/bin/bash
set -e

REPO="/home/sc/repos/polytopia-clone"
SERVE_BIN="$REPO/node_modules/.bin/serve"
cd "$REPO" 2>/dev/null || { echo "REPO_NOT_FOUND"; exit 1; }

BUILD_OUTPUT=$(npm run build 2>&1)
BUILD_OK=$(echo "$BUILD_OUTPUT" | grep -c "built in")
echo "BUILD:$BUILD_OK"

TEST_OUTPUT=$(npx vitest run 2>&1)
TESTS_PASSED=$(echo "$TEST_OUTPUT" | grep -oP 'Tests\s+\d+ passed' | head -1)
echo "TESTS:$TESTS_PASSED"

if [ "$BUILD_OK" -eq 0 ]; then
  echo "BUILD_FAILED"
  echo "$BUILD_OUTPUT" | tail -5
  exit 1
fi

# Server health check — list and kill stale processes
PIDS=$(lsof -ti:3001 2>/dev/null || true)
if [ -n "$PIDS" ]; then
  for pid in $PIDS; do
    kill "$pid" 2>/dev/null && echo "KILLED_PID:$pid"
  done
  sleep 1
fi

if curl -sf http://localhost:3001/ > /dev/null 2>&1; then
  echo "SERVER:OK"
else
  echo "SERVER:RESTARTING"
  nohup "$SERVE_BIN" dist -p 3001 --cors > /tmp/polytopia-preview.log 2>&1 &
  sleep 3
  if curl -sf http://localhost:3001/ > /dev/null 2>&1; then
    echo "SERVER:RESTARTED_OK"
  else
    echo "SERVER:FAILED"
    cat /tmp/polytopia-preview.log | tail -5
    exit 1
  fi
fi

echo "DEPLOY_OK"
