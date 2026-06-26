#!/bin/bash
# hermes-webui-tunnel-restart.sh
# Restart cloudflared tunnel for hermes-webui — run via cron or manually.
# No sudo required. Safe to re-run.
#
# Usage:
#   chmod +x hermes-webui-tunnel-restart.sh
#   ./hermes-webui-tunnel-restart.sh          # dry-run logic
#   nohup ./hermes-webui-tunnel-restart.sh & # background

set -euo pipefail

BIN="/tmp/cloudflared"
CRED="/opt/data/cloudflared/hermes-webui-creds.json"
TUNNEL_NAME="hermes-webui"
TARGET="http://172.19.0.2:8787"
LOG="${LOG:-/tmp/hermes-tunnel.log}"

# Allow log override via env (e.g. from cron: LOG=/opt/data/logs/hermes-webui-tunnel.log ./restart.sh)
# For cron: set in crontab: LOG=/opt/data/logs/hermes-webui-tunnel.log */5 * * * * /opt/data/scripts/hermes-webui-tunnel-restart.sh

log() { echo "[$(date '+%Y-%m-%dT%H:%M:%SZ')] $*" >> "$LOG"; }

restart_tunnel() {
    local pid
    log "Restarting cloudflared tunnel..."

    # Kill any existing cloudflared process for this tunnel
    pkill -f "cloudflared.*$TUNNEL_NAME" 2>/dev/null || true
    sleep 2

    # Start fresh
    nohup "$BIN" tunnel run \
        --credentials-file "$CRED" \
        --url "$TARGET" \
        "$TUNNEL_NAME" \
        >> "$LOG" 2>&1 &

    pid=$!
    log "Tunnel restarted with PID $pid"
    echo "Started PID $pid"
}

# Main logic
if pgrep -f "cloudflared.*$TUNNEL_NAME" > /dev/null 2>&1; then
    log "Tunnel is running — no restart needed"
    echo "Running"
else
    log "Tunnel not running"
    restart_tunnel
fi