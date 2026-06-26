# HWC Build + Deploy Pattern

**Applies to:** `hermes-web-computer` (HWC) project.

## Go Toolchain in Container

```
GOPATH=/home/hermeswebui/.hermes/home/go \
  /home/hermeswebui/.hermes/home/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.26.0.linux-amd64/bin/go
```

## Deploy: Build → Copy → Restart

```bash
# Build
cd /home/hermeswebui/.hermes/hermes-web-computer/backend && \
GOPATH=/home/hermeswebui/.hermes/home/go \
  /home/hermeswebui/.hermes/home/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.26.0.linux-amd64/bin/go \
  build -o /tmp/hwc-server ./cmd/server/

# Copy (NOT scp — pipe it)
cat /tmp/hwc-server | ssh -i /home/hermeswebui/.hermes/container_key \
  -o StrictHostKeyChecking=no -o ConnectTimeout=10 \
  sean@172.19.0.1 "cat > /tmp/hwc-server && chmod +x /tmp/hwc-server"

# Restart
ssh -i /home/hermeswebui/.hermes/container_key \
  -o StrictHostKeyChecking=no -o ConnectTimeout=10 \
  sean@172.19.0.1 'kill $(lsof -t -i:3005) 2>/dev/null; sleep 1; cd /home/sean/.hermes/hermes-web-computer/backend && HERMES_HWC_ROOT=/home/sean/.hermes/hermes-web-computer nohup /tmp/hwc-server server --port 3005 > /tmp/hwc-server.log 2>&1 & sleep 3; curl -s -o /dev/null -w "%{http_code}" http://localhost:3005/'
```

## Deploy Frontend

```bash
cd frontend && npm run build && tar czf /tmp/hwc-frontend.tar.gz -C frontend dist/ && \
cat /tmp/hwc-frontend.tar.gz | ssh -i /home/hermeswebui/.hermes/container_key \
  -o StrictHostKeyChecking=no -o ConnectTimeout=10 \
  sean@172.19.0.1 "tar xzf - -C /home/sean/.hermes/hermes-web-computer/frontend/"
```

## Git Hygiene

**Never `git add -A`** in HWC repo — stages .npm-cache, .playwright (~500MB), .gopath, etc.
Always stage selectively: `git add backend/... frontend/...`

## Server Info

- Port: 3005 | Binary: /tmp/hwc-server | Log: /tmp/hwc-server.log
- Env: HERMES_HWC_ROOT=/home/sean/.hermes/hermes-web-computer
