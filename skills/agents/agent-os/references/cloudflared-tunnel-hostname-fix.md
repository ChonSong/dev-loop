# Cloudflared Tunnel Hostname Mismatch

## Problem

The cloudflared container is configured with `--url http://backend:3001` (docker-compose service name). But all agent-os containers are launched via `docker run` (not `docker compose up`), so the container names are `agent-os-backend`, not `backend`.

Result: cloudflared connects to Cloudflare edge successfully (logs show "Registered tunnel connection") but cannot reach the backend — DNS resolution for `backend` fails inside the `agent-os_agent-net` network.

## Evidence

```
# Cloudflared is running and connected
$ docker logs agent-os-cloudflared 2>&1 | tail -3
Registered tunnel connection connIndex=0 ... location=mel01 protocol=quic
```

But the compose config has:
```yaml
command: ["tunnel", "run", "--token-file", "/etc/cloudflared/agent-os-argo-token.txt", "--url", "http://backend:3001"]
```

And the actual backend container is named `agent-os-backend`:
```
$ docker ps --filter name=agent-os-backend
agent-os-backend   Up 10 hours (healthy)
```

## Fix Options

### Option A: Add network alias to backend (preferred — no cloudflared restart)

Recreate backend with `--network-alias backend`:
```bash
docker stop agent-os-backend && docker rm agent-os-backend
docker run -d \
  --name agent-os-backend \
  --network-alias backend \
  --network agent-os_agent-net \
  ... (all other args)
```

Then `backend:3001` resolves to the agent-os-backend container.

### Option B: Update cloudflared command

Change the cloudflared run command to use `agent-os-backend:3001`:
```bash
docker stop agent-os-cloudflared && docker rm agent-os-cloudflared
docker run -d \
  --name agent-os-cloudflared \
  --restart unless-stopped \
  --network agent-os_agent-net \
  cloudflare/cloudflared:2026.3.0 \
  tunnel run --token-file /etc/cloudflared/agent-os-argo-token.txt --url http://agent-os-backend:3001
```

### Option C: Switch to docker compose for all services

This would make service names work natively, but `docker compose up -d` has been observed to hang on this host.
