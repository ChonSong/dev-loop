#!/bin/bash
CLOUDFLARED=/home/sean/.hermes/bin/cloudflared
LOGDIR=/home/sean/.hermes/logs
mkdir -p 

# Ensure binary exists
if [ ! -f  ]; then
    curl -sL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o 
    chmod +x 
fi

# Start hermes-webui tunnel if not running
if ! pgrep -f cloudflared.*hermes-webui-creds > /dev/null 2>&1; then
    pkill -f cloudflared.*config.yml 2>/dev/null
    sleep 1
    nohup  --no-autoupdate tunnel --config /home/sean/.hermes/cloudflared/config.yml >> /hermes-webui-tunnel.log 2>&1 &
    echo [Wed Jun 3 02:42:47 UTC 2026] Started hermes-webui tunnel >> /watchdog.log
fi

# Start onetag tunnel if not running
if ! pgrep -f cloudflared.*onetag-tunnel-creds > /dev/null 2>&1; then
    pkill -f cloudflared.*onetag-config 2>/dev/null
    sleep 1
    nohup  --no-autoupdate tunnel --config /home/sean/.hermes/cloudflared/onetag-config.yml >> /onetag-tunnel.log 2>&1 &
    echo [Wed Jun 3 02:42:47 UTC 2026] Started onetag tunnel >> /watchdog.log
fi
