# Cloudflared Tunnel Hostname Fix

## Problem

The cloudflared tunnel container was configured with `backend:3001` as the target URL (from the original docker-compose service name), but containers are launched via `docker run` with the container name `agent-os-backend`. Docker's internal DNS doesn't resolve `backend` because it's not a compose service name.

## Solution

Add `--network-alias backend` to the backend's `docker run` command so both `backend` and `agent-os-backend` resolve on the `agent-os_agent-net` network:

```bash
docker run -d \
  --name agent-os-backend \
  --network agent-os_agent-net --network-alias backend \
  ...
```

Alternatively, update the cloudflared tunnel token/config to use `agent-os-backend:3001` instead of `backend:3001`.

## Verification

```bash
# Check if both names resolve
docker exec agent-os-cloudflared sh -c 'nslookup backend && nslookup agent-os-backend'

# Check tunnel logs for successful connections
docker logs agent-os-cloudflared 2>&1 | grep -i 'registered\|connection'
```

## Current Status (as of 2026-05-10)

The fix has been identified but not yet applied. The tunnel is connected but cannot reach the backend because `backend:3001` doesn't resolve. The cloudflared container shows "Registered tunnel connection" in logs but the tunnel cannot proxy requests.
