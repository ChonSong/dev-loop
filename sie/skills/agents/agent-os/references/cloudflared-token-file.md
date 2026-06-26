# cloudflared Token File — Silent Exit Bug

## Symptom

`agent-os-cloudflared` container shows status `exited` immediately after starting, with no error in `docker logs`.

## Root Cause

The cloudflared Docker image has **no `sh` binary**. When `--token-file` points to a missing or unreadable file, cloudflared tries to `exec("sh")` to read it. The exec fails silently because `sh` doesn't exist, and the container exits with no logged error.

**Diagnosis:**
```bash
# Container is stopped:
docker inspect agent-os-cloudflared --format '{{.State.Status}}'
# → exited

# Logs show nothing useful:
docker logs agent-os-cloudflared
# → (empty or just startup banner)

# Inspect the command to confirm token-file path:
docker inspect agent-os-cloudflared --format '{{json .Config.Cmd}}'
# → ["tunnel","run","--token-file","/etc/cloudflared/agent-os-argo-token.txt","--url","http://backend:3001"]

# Verify the token file exists on host:
ls -la /home/sean/.cloudflared/agent-os-argo-token.txt
```

## Fix

Recreate the tunnel token via Cloudflare API and save it to the host path:

```bash
# 1. Get a Cloudflare API token with tunnels:create + tunnels:read permissions (cfat_...)
CFAT_TOKEN="your_cloudflare_access_token"
ACCOUNT_ID="your_cloudflare_account_id"

# 2. Create new tunnel (or reuse existing one by fetching credentials)
TUNNEL_RESP=$(curl -s -X POST "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/tunnels" \
  -H "Authorization: Bearer ${CFAT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"name": "agent-os-argo", "tunnel_type": "argo_tunnel"}')

# Extract the JWT token:
echo "$TUNNEL_RESP" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['result']['created_token'])"

# 3. Save token to host (JWT is ~240 bytes — use Python to avoid SSH echo truncation):
python3 -c "
import sys
token = sys.stdin.read().strip()
with open('/home/sean/.cloudflared/agent-os-argo-token.txt', 'w') as f:
    f.write(token)
print(f'Saved {len(token)} byte token')
"

# 4. Restart cloudflared container
docker compose -f /home/sean/.hermes/agent-os/docker-compose.yml up -d cloudflared
```

## Prevention

The token file must be:
- Mounted read-only into the container at `/etc/cloudflared/agent-os-argo-token.txt`
- Present on the host at `/home/sean/.cloudflared/agent-os-argo-token.txt`
- Owned by the user running Docker (readable by Docker daemon)

## Note on cloudflared Image Shell

The `cloudflare/cloudflared` Docker image is built from scratch and contains no shell. This means:
- `docker exec` with `sh` or `bash` will fail
- Debug commands like `docker exec agent-os-cloudflared cat /etc/cloudflared/...` won't work
- Use `docker cp` to extract files from the container instead if needed
