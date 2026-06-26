#!/usr/bin/env bash
set -euo pipefail

# Usage: bash migrate-to-host.sh
# Migrate a Docker containerized service to native systemd on the host.
# Place this on a shared bind-mount path so the host can execute it.
#
# Prerequisites (handled by script):
#   - Service binary/tool installed on host (pip/uv)
#   - Docker running on host (to stop old container)
#   - systemd user services enabled

# --- Config ---
SERVICE_NAME="${SERVICE_NAME:-my-service}"
SERVICE_BINARY="${SERVICE_BINARY:-$HOME/.local/bin/$SERVICE_NAME}"
SERVICE_HOME="${SERVICE_HOME:-$HOME/.$SERVICE_NAME}"
DOCKER_CONTAINER="${DOCKER_CONTAINER:-$SERVICE_NAME}"
SERVICE_PORT="${SERVICE_PORT:-9119}"

# --- 1. Install ---
if ! command -v "$SERVICE_BINARY" &>/dev/null; then
    echo "Installing $SERVICE_NAME..."
    uv tool install "$SERVICE_NAME" || pip3 install "$SERVICE_NAME"
fi

# --- 2. Create systemd service ---
mkdir -p "$HOME/.config/systemd/user"

cat > "$HOME/.config/systemd/user/$SERVICE_NAME.service" << UNIT
[Unit]
Description=$SERVICE_NAME
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=$SERVICE_BINARY
Restart=always
RestartSec=5
Environment=HOME=$SERVICE_HOME

[Install]
WantedBy=default.target
UNIT

# Optional: dashboard/web UI service
if [ -n "$SERVICE_PORT" ]; then
  cat > "$HOME/.config/systemd/user/$SERVICE_NAME-dashboard.service" << UNIT
[Unit]
Description=$SERVICE_NAME Dashboard
After=$SERVICE_NAME.service

[Service]
Type=simple
ExecStart=$SERVICE_BINARY dashboard --port $SERVICE_PORT
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
UNIT
fi

systemctl --user daemon-reload

# --- 3. Stop Docker container ---
if command -v docker &>/dev/null; then
    if docker ps --format '{{.Names}}' | grep -qx "$DOCKER_CONTAINER"; then
        echo "Stopping Docker container '$DOCKER_CONTAINER'..."
        docker stop "$DOCKER_CONTAINER"
        docker update --restart=no "$DOCKER_CONTAINER" 2>/dev/null || true
    fi
fi

# --- 4. Start via systemd ---
systemctl --user enable --now "$SERVICE_NAME.service" 2>/dev/null
systemctl --user enable --now "$SERVICE_NAME-dashboard.service" 2>/dev/null || true

sleep 2

# --- 5. Verify ---
if systemctl --user is-active --quiet "$SERVICE_NAME.service"; then
    echo "✓ $SERVICE_NAME is running via systemd"
else
    echo "✗ $SERVICE_NAME failed to start"
    systemctl --user status "$SERVICE_NAME.service" --no-pager | head -10
fi

echo ""
echo "--- Revert ---"
echo "systemctl --user stop $SERVICE_NAME $SERVICE_NAME-dashboard"
echo "docker start $DOCKER_CONTAINER"
