# agent-os SSH Path Correction

## Critical SSH Key Path

**Wrong**: `/opt/data/home/.hermes/home/.ssh/id_ed25519`
**Correct**: `/opt/data/home/.ssh/id_ed25519`

The `.hermes/home/` segment is incorrect — the key lives directly under `/opt/data/home/.ssh/`.

## Why This Matters

Many older skill references, memory entries, and cron job scripts may have the wrong path. Always use:
```bash
ssh -i /opt/data/home/.ssh/id_ed25519 sean@localhost "<command>"
```

## Host SSH Status

Port 22 on hpprobook is occupied by an unidentified process. SSH works on port 2229:
```bash
ssh -i /opt/data/home/.ssh/id_ed25519 -p 2229 root@localhost "hostname"
```

See `hermes-docker-workflow/references/ssh-host-access-debugging.md` for full troubleshooting details.

## Build + Deploy SSH Commands

All host commands go through Docker socket from hermes container, not direct SSH (since port 22 is blocked):
```bash
# Build via docker exec (not SSH)
docker exec -e NODE_PATH=/app/node_modules agent-os-backend \
  /app/node_modules/.bin/vite build /home/sean/.hermes/agent-os/apps/dashboard/frontend

# Deploy via docker cp (not SSH)
docker cp agent-os-backend:/path/to/dist/. /home/sean/.hermes/agent-os-patched/frontend-dist/assets/

# Restart
docker restart agent-os-backend
```

Direct SSH to host (`ssh sean@localhost`) is unreliable — use the Docker socket approach instead: `docker -H unix:///var/run/docker.sock exec ...`