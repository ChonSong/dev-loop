# HWC v1.4 Build Verification

## Go Build (backend/)
```bash
cd /home/sean/.hermes/hermes-web-computer/backend && go build ./...
```

NOT `go build ./...` from repo root — go.mod is in the `backend/` subdirectory.

## Frontend Build
```bash
cd /home/sean/.hermes/hermes-web-computer/frontend && npm run build
```

Takes ~48s. No go installation needed for frontend.

## Full Stack Build
```bash
# Frontend
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 \
  'cd /home/sean/.hermes/hermes-web-computer/frontend && npm run build 2>&1 | tail -5'

# Backend  
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 \
  'cd /home/sean/.hermes/hermes-web-computer/backend && go build ./...'
```

## Go Server Binary
```bash
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 \
  'cd /home/sean/.hermes/hermes-web-computer/backend && go build -o /tmp/hwc-server ./cmd/server/'
```

Runs on port 3005 by default.

## Common Issues

| Issue | Fix |
|-------|-----|
| `go: cannot find main module` | `cd backend/` before running go commands |
| Subagent timeout on HWC | Do builds yourself after subagent completes |
| Go build fails on new machine | `cd backend && go mod tidy` |
| Frontend dist not updating | `rm -rf frontend/dist && npm run build` |