# Container Access Patterns — HWC
**Created**: 2026-06-03 | **Updated**: 2026-06-08

## Container Topology

| Container | Role | HWC Repo Path | SSH to Host |
|-----------|------|---------------|-------------|
| `hermes-webui` (this env) | WebUI, agent sessions, cron jobs | `/home/hermeswebui/.hermes/hermes-web-computer` | ✅ Has `container_key` at `/home/hermeswebui/.hermes/container_key` |
| EndeavourOS host | Canonical repo, builds, Chrome | `/home/sean/.hermes/hermes-web-computer` | N/A (is host) |

**Note**: The old `/opt/data/hermes-web-computer` path is DEAD. Use `/home/hermeswebui/.hermes/hermes-web-computer` in this container.

## What Works From This Container

```bash
# File system checks
cd /home/hermeswebui/.hermes/hermes-web-computer
test -f frontend/dist/index.html  # frontend build exists
git log --oneline -1              # latest commit
git status --short                # dirty files

# Go build and test (Go IS installed in this container)
cd backend
GOPATH=/home/hermeswebui/.hermes/home/go \
  /home/hermeswebui/.hermes/home/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.26.0.linux-amd64/bin/go \
  build -o /tmp/hwc-server ./cmd/server/

# Run tests
GOPATH=/home/hermeswebui/.hermes/home/go \
  /home/hermeswebui/.hermes/home/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.26.0.linux-amd64/bin/go \
  test ./... -count=1 -timeout=120s

# Copy binary to host (pipe pattern — SCP may timeout)
cat /tmp/hwc-server | ssh -i /home/hermeswebui/.hermes/container_key \
  -o StrictHostKeyChecking=no -o ConnectTimeout=10 \
  sean@172.19.0.1 "cat > /tmp/hwc-server && chmod +x /tmp/hwc-server"

# Network — host is reachable at 172.19.0.1
curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://172.19.0.1:3005/
```

## What Does NOT Work

- **Docker from container**: Not installed
- **systemd from container**: Not available
- **Playwright browser tests from container**: Chromium not installed (use `npx playwright install` or run on host)

## SSH Key

The SSH key for reaching the host is at:
```
/home/hermeswebui/.hermes/container_key
```

Old references to `/home/hermes/.ssh/id_ed25519` are STALE — that path does not exist in this container.

## Host Port Reference

| Service | Port | Health Check |
|---------|------|-------------|
| Hermes Gateway | 8787 | `curl http://172.19.0.1:8787/health` |
| HWC Server | 3005 | `curl http://172.19.0.1:3005/` → 200 |
| agent-os (legacy) | 3001 | May still be running — check with `lsof -i:3001` |
