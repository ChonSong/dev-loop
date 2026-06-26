# agent-deploy.sh — Host-side GHCR Polling Deploy Script

## Status (2026-05-06)

Working. 10+ consecutive CI runs green. Server polling every 60s. DNS tunnel live at `https://agent-os.codeovertcp.com`.

## Placement
- Script: `/home/sean/scripts/agent-deploy.sh` on the host
- Digest tracking: `/tmp/agent-os-prev-digest`
- Log: `/tmp/agent-os-deploy.log`

## Cron
```
* * * * * /home/sean/scripts/agent-deploy.sh >> /tmp/agent-os-deploy.log 2>&1
```
(Cron runs every minute, script itself skips silently if digest unchanged.)

## Script
```bash
#!/bin/bash
# agent-deploy.sh — polls GHCR for new image digest and redeploys
set -e

PREV_DIGEST_FILE="/tmp/agent-os-prev-digest"
PREV_DIGEST=$(cat "$PREV_DIGEST_FILE" 2>/dev/null || echo '')
PREV_DIGEST=${PREV_DIGEST:1}  # strip leading newline if any

# Pull latest and get its digest
docker pull ghcr.io/chonsong/agent-os:latest >/dev/null 2>&1
CURRENT_DIGEST=$(docker images --no-trunc ghcr.io/chonsong/agent-os:latest --format '{{.ID}}' | head -1)

if [ -z "$CURRENT_DIGEST" ]; then
  echo "[$(date)] Could not get image digest, skipping"
  exit 0
fi

if [ "$CURRENT_DIGEST" = "$PREV_DIGEST" ]; then
  exit 0  # silent — no change
fi

echo "[$(date)] New image: ${CURRENT_DIGEST:0:12} (was: ${PREV_DIGEST:0:12})"
echo "$CURRENT_DIGEST" > "$PREV_DIGEST_FILE"

cd /home/sean/.hermes/agent-os
docker-compose pull >/dev/null 2>&1
docker-compose up -d
echo "[$(date)] Redeployed ghcr.io/chonsong/agent-os:latest"
```

## Key Decisions

- `docker-compose pull` (explicit, silent) followed by `docker-compose up -d` — pulls ALL service images, then starts all. No `--pull always` needed since image is pre-pulled.
- `docker images --no-trunc ... --format '{{.ID}}'` to get full digest — works reliably across Docker versions.
- Digest file at `/tmp/agent-os-prev-digest` — minimal footprint, survives reboots.
- `&&` chaining ensures any step failure aborts the script (set -e).

## Why This Architecture

**Core problem:** `docker pull` from inside a container using `/var/run/docker.sock` fails because the container's network namespace cannot reach GHCR (Docker socket mount gives file access but network remains container-scoped).

**Solution:** Host cron runs the script directly — host network can reach GHCR.
