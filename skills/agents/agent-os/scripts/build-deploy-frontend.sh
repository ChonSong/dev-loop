#!/usr/bin/env bash
# build-deploy-frontend.sh — Build and deploy Bento-patched frontend to agent-os
# Run from within the agent-os-backend container via SSH
#
# Usage: docker exec agent-os-backend bash /tmp/build-deploy-frontend.sh
#
# Prerequisites:
#   - Source files patched in /home/sean/.hermes/agent-os/apps/dashboard/frontend/src/
#   - Patched dist dir on host at /home/sean/.hermes/agent-os-patched/frontend-dist/
#   - Volume mount override already in docker-compose.yml
#
# This script:
#   1. Builds frontend with vite (NODE_PATH=/app/node_modules)
#   2. Copies built assets to the persistent host directory
#   3. Restarts backend to pick up changes

set -e

SRC="/home/sean/.hermes/agent-os/apps/dashboard/frontend"
HOST_PATCHED="/home/sean/.hermes/agent-os-patched/frontend-dist"
CONTAINER_APP="/app/apps/dashboard/frontend/dist"

echo "=== Building frontend ==="
cd /home/sean/.hermes/agent-os
NODE_PATH=/app/node_modules /app/node_modules/.bin/vite build "$SRC" 2>&1 | tail -5

BUNDLE=$(ls "$SRC/dist/assets/"index-*.js | xargs basename | head -1)
CSS=$(ls "$SRC/dist/assets/"index-*.css | xargs basename | head -1)
echo "Built: $BUNDLE + $CSS"

echo "=== Copying to persistent host dir ==="
rm -f "$HOST_PATCHED/assets/"*
cp "$SRC/dist/assets/$CSS" "$HOST_PATCHED/assets/"
cp "$SRC/dist/assets/$BUNDLE" "$HOST_PATCHED/assets/"
cp "$SRC/dist/index.html" "$HOST_PATCHED/"

echo "=== Restarting backend ==="
cd /home/sean/.hermes/agent-os && docker compose restart backend
echo "Done. Frontend at http://localhost:1331"
