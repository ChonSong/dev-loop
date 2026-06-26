#!/bin/bash
CF=/home/sean/.hermes/bin/cloudflared
LOGDIR=/home/sean/.hermes/logs
mkdir -p $LOGDIR

pkill -f 'cloudflared.*config' 2>/dev/null
sleep 2

nohup $CF --no-autoupdate tunnel --config /home/sean/.hermes/cloudflared/config.yml run > $LOGDIR/hermes-webui-tunnel.log 2>&1 &
echo "hermes-webui: $!"

nohup $CF --no-autoupdate tunnel --config /home/sean/.hermes/cloudflared/onetag-config.yml run > $LOGDIR/onetag-tunnel.log 2>&1 &
echo "onetag: $!"

sleep 5
ps aux | grep cloudflared | grep -v grep
