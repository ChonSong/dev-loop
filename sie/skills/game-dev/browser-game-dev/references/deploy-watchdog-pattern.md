# No-Agent Deploy Watchdog Pattern

## Pattern

A cron job with `no_agent=true` runs a shell script on schedule. No LLM is involved — the script's stdout is delivered verbatim. Empty output = silent delivery (nothing sent). Non-zero exit sends an error alert.

This is the right pattern for:
- **Build + test + health check loops** — rebuild on source changes, restart if down
- **Watchdog alerts** — "game server is down," "disk is full," "memory threshold exceeded"
- **Data collection** — poll an API and pipe the result into a message

## Cron Job Setup

```bash
# Create the script
cat > ~/.hermes/scripts/deploy-watchdog.sh << 'SCRIPT'
#!/bin/bash
set -e
cd /home/sc/repos/my-game

BUILD_OK=$(npm run build 2>&1 | grep -c "built in")
TESTS_PASSED=$(npx vitest run 2>&1 | grep -oP 'Tests\s+\d+ passed')

echo "BUILD:$BUILD_OK"
echo "TESTS:$TESTS_PASSED"

if [ "$BUILD_OK" -eq 0 ]; then
  echo "BUILD_FAILED"
  echo "$BUILD_OUTPUT" | tail -5
  exit 1
fi

if curl -sf http://localhost:3001/ > /dev/null 2>&1; then
  echo "SERVER:OK"
else
  echo "SERVER:RESTARTING"
  # Kill any stale processes on the port to prevent accumulation
  for pid in $(lsof -ti:3001 2>/dev/null); do
    kill "$pid" 2>/dev/null && echo "KILLED_PID:$pid"
  done
  sleep 1
  cd /home/sc/repos/my-game && nohup npx serve dist -p 3001 --cors > /tmp/preview.log 2>&1 &
  sleep 3
  if curl -sf http://localhost:3001/ > /dev/null 2>&1; then
    echo "SERVER:RESTARTED_OK"
  else
    echo "SERVER:FAILED"
    exit 1
  fi
fi

echo "DEPLOY_OK"
SCRIPT
chmod +x ~/.hermes/scripts/deploy-watchdog.sh
```

Create the cron job (via cronjob tool):

```
action: create
name: My Game deploy loop
no_agent: true
schedule: "every 5m"
script: deploy-watchdog.sh
```

## Delivery Semantics with no_agent=true

| Output | Result |
|--------|--------|
| Non-empty stdout | Sent verbatim to the delivery target |
| Empty stdout | Silent — nothing sent, user sees nothing |
| Non-zero exit | Error alert sent |
| Timeout | Error alert sent |

Design scripts to stay quiet when there's nothing to report (the classic watchdog pattern).

## Chaining Jobs

Use `context_from` to chain a no-agent data collector with an LLM summarizer:

1. Job A (no_agent=true): polls API, writes result to stdout
2. Job B (no_agent=false, default): reads Job A's last output via `context_from: [<job-a-id>]`, summarizes it
