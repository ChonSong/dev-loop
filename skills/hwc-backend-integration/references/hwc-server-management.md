# HWC Server Management (from Container)

## Starting the HWC Server

The HWC server runs on the EndeavourOS host at port 3005. The container has SSH access via `container_key`.

### Build in Container, Deploy to Host

```bash
# 1. Build in container (Go is available)
cd /home/hermeswebui/.hermes/hermes-web-computer/backend
GOPATH=/home/hermeswebui/.hermes/home/go \
  /home/hermeswebui/.hermes/home/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.26.0.linux-amd64/bin/go \
  build -o /tmp/hwc-server ./cmd/server/

# 2. Copy binary to host (SCP may timeout; use pipe instead)
cat /tmp/hwc-server | ssh -i /home/hermeswebui/.hermes/container_key \
  -o StrictHostKeyChecking=no -o ConnectTimeout=10 \
  sean@172.19.0.1 "cat > /tmp/hwc-server && chmod +x /tmp/hwc-server"

# 3. Start server on host
ssh -i /home/hermeswebui/.hermes/container_key \
  -o StrictHostKeyChecking=no -o ConnectTimeout=10 \
  sean@172.19.0.1 "cd /home/sean/.hermes/hermes-web-computer/backend && \
  HERMES_HWC_ROOT=/home/sean/.hermes/hermes-web-computer \
  nohup /tmp/hwc-server server --port 3005 > /tmp/hwc-server.log 2>&1 & \
  sleep 3 && curl -s -o /dev/null -w '%{http_code}' http://localhost:3005/"
```

Key facts:
- Uses `PORT` env var (NOT `--port` flag) — `--port 3005` does NOT work
- `HERMES_HWC_ROOT` must point to the project directory on the host
- Binary location on host: `/home/sean/.hermes/hermes-web-computer/backend/agent-os` (or `/tmp/hwc-server` for temp)
- Health check: `curl -s -o /dev/null -w "%{http_code}" http://172.19.0.1:3005/` → expect 200
- WS endpoint: `curl -s -o /dev/null -w "%{http_code}" http://172.19.0.1:3005/ws` → expect 426 (upgrade required)

### Restarting the Server

```bash
ssh -i /home/hermeswebui/.hermes/container_key \
  -o StrictHostKeyChecking=no -o ConnectTimeout=10 \
  sean@172.19.0.1 "kill \$(lsof -t -i:3005) 2>/dev/null; sleep 1; \
  cd /home/sean/.hermes/hermes-web-computer/backend && \
  HERMES_HWC_ROOT=/home/sean/.hermes/hermes-web-computer \
  nohup /tmp/hwc-server server --port 3005 > /tmp/hwc-server.log 2>&1 & \
  sleep 3 && ss -tlnp | grep 3005"
```

### Verifying Server Health

```bash
ssh -i /home/hermeswebui/.hermes/container_key \
  -o StrictHostKeyChecking=no sean@172.19.0.1 \
  "curl -s -o /dev/null -w '%{http_code}' http://localhost:3005/ && \
   curl -s http://localhost:3005/ | head -5"
```

## Binary Swap Deployment

```bash
ssh host "kill \$(lsof -t -i:3005) 2>/dev/null; sleep 2"
ssh host "cp /tmp/hwc-server /home/sean/.hermes/hermes-web-computer/backend/agent-os"
ssh host "cd /home/sean/.hermes/hermes-web-computer/backend && \
  HERMES_HWC_ROOT=/home/sean/.hermes/hermes-web-computer \
  nohup ./agent-os server --port 3005 > /tmp/hwc-server.log 2>&1 &"
```

## Pitfalls

- **SCP timeout**: Use `cat file | ssh host "cat > file"` pipe pattern for large binaries
- **`--port` flag doesn't work**: Must use `PORT=3005` env var
- **Stale process**: Always `lsof -i:3005` before starting
- **Audio bridge error**: Expected when Fun-Audio-Chat isn't running — not a blocker
- **Static files not served**: Must start from `backend/` dir so `../frontend/dist` resolves
- **Git bloat**: Run `git diff --cached --stat` before committing; .playwright/, .npm-cache/, agentos binary can bloat commits
