#!/bin/bash
# hwc-visual-qa.sh — Container-side wrapper for HWC Visual QA
# SSHs to host and runs hwc-host-visual-qa.sh natively (Chrome available there)

SSH_HOST="sean@172.19.0.1"
HOST_SCRIPT="/home/sc/.hermes/scripts/hwc-host-visual-qa.sh"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S UTC')

echo "[$TIMESTAMP] HWC Visual QA (via SSH to host)"

# Quick health check first
HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" "http://172.19.0.1:3005/" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" != "200" ]; then
  echo "RESULT: FAIL"
  echo "Server at 172.19.0.1:3005 returned HTTP $HTTP_CODE"
  echo "Expected 200. Server may be down."
  exit 1
fi

# Run the host-side QA script
ssh "$SSH_HOST" "bash $HOST_SCRIPT" 2>&1
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
  echo "Host QA script exited with code $EXIT_CODE"
fi

exit $EXIT_CODE
