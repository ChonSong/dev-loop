# CI SSH Deploy Setup

## Current State
CI workflow has SSH-based deploy step in `.github/workflows/agent-os.yml`. It SSHs to the host, pulls the latest GHCR image, and recreates containers.

## Required GitHub Secrets

### DEPLOY_KEY
The SSH private key for CI to authenticate to the host:
```bash
# On host, the key already exists:
cat /home/sean/.ssh/id_ed25519_ci_deploy
# Public key is already in /home/sean/.ssh/authorized_keys
```

Set as GitHub secret:
```bash
gh secret set DEPLOY_KEY < /home/sean/.ssh/id_ed25519_ci_deploy
# Or via GitHub UI: Settings → Secrets → Actions → New repository secret
```

### DEPLOY_HOST
The host's public IP or hostname:
```bash
gh secret set DEPLOY_HOST -b "your.host.ip.or.domain"
```

## Graceful Degradation
If secrets aren't set, the deploy step prints a warning and exits 0 — CI doesn't fail, deploy is just skipped.

## What the deploy does
1. Pulls `ghcr.io/chonsong/agent-os:latest`
2. Stops and removes `agent-os-backend` + `agent-os-webhook-emitter`
3. Recreates both with `docker run` (correct env vars, volumes, health checks)
4. Waits for backend health check to pass
5. Syncs frontend-dist from image to host volume mount
