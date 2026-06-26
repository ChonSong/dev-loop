#!/usr/bin/env bash
# Start Tandem Browser with shared session for Hermes AI viewer.
set -e

cd /home/sc/repos/tandem-browser

# Kill anything on ports 9222 and 3099
lsof -ti :9222 2>/dev/null | xargs -r kill 2>/dev/null || true
lsof -ti :3099 2>/dev/null | xargs -r kill 2>/dev/null || true
sleep 1

# Launch Electron with remote debugging port 9222
export DISPLAY=:0
nohup node_modules/electron/dist/electron . \
  --no-sandbox \
  --remote-debugging-port=9222 \
  --remote-allow-origins=* \
  > /tmp/tandem-debug.log 2>&1 &

echo "Tandem starting with remote debugging on port 9222..."

# Wait for CDP to be ready
for i in $(seq 1 15); do
  if curl -s http://127.0.0.1:9222/json/version > /dev/null 2>&1; then
    echo "CDP ready after ${i}s"
    break
  fi
  sleep 1
done

# Start the electron viewer
NODE_PATH=./node_modules nohup node scripts/electron-viewer.js \
  > /tmp/electron-viewer.log 2>&1 &

echo "Electron viewer starting at http://localhost:3099"
