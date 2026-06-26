# Docker Alpine Python: PEP 668 + ENTRYPOINT Conflicts

## PEP 668 — System-wide pip blocked on Debian/Ubuntu

**Symptom**: `docker build` fails with:
```
error: externally-managed-environment
× This environment is externally managed
[... pip blocked by PEP 668 ...]
```

**Cause**: Debian/Ubuntu Python 3.11+ marks the system Python as managed. Alpine Linux (used by `node:22-alpine` base images) does NOT have this restriction, but many Docker Hub images derive from Debian and include the PEP 668 marker.

**Fix** (pick one):

### Option A: Override with `--break-system-packages` (preferred for alpine)
```dockerfile
RUN pip install --no-cache-dir --break-system-packages <package>
```

### Option B: Use a virtual environment
```dockerfile
RUN python -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir <package>
ENV PATH="/opt/venv/bin:$PATH"
```

### Option C: Delete the PEP 668 marker (Debian images)
```dockerfile
RUN rm -f /usr/lib/python3.*/EXTERNALLY-MANAGED
```

## ENTRYPOINT Conflict with base image entrypoints

**Symptom**: Container starts but CMD is ignored or logs show `docker-entrypoint.sh` corruption.

**Cause**: Base images like `node:alpine`, `python:alpine`, etc. ship with a shell script entrypoint (`/usr/local/bin/docker-entrypoint.sh`) that runs before the Dockerfile's CMD. When the Dockerfile CMD is JSON array format (`["node", "script.js"]`), the shell script receives arguments incorrectly.

**Evidence**:
```bash
# Container exits immediately or behaves wrong
docker logs <container>
# Shows: sh: can't exec 'node': No such file or directory
```

Or the shell entrypoint script is visible in the container:
```bash
docker exec <container> cat /usr/local/bin/docker-entrypoint.sh
```

**Fix — override ENTRYPOINT explicitly**:
```dockerfile
# After FROM line, remove the inherited entrypoint
RUN rm -f /usr/local/bin/docker-entrypoint.sh
# OR override it
ENTRYPOINT []
CMD ["node", "server.js"]
```

**For `node:22-alpine` specifically**:
```dockerfile
FROM node:22-alpine
# Kill the inherited entrypoint that conflicts with CMD
ENTRYPOINT ["/bin/sh", "-c"]
# Or better: remove it
RUN rm -f /usr/local/bin/docker-entrypoint.sh
ENTRYPOINT []
CMD ["node", "index.js"]
```

## Combined fix example (alpine + Python + Node)

```dockerfile
FROM node:22-alpine

# Remove conflicting base image entrypoint
RUN rm -f /usr/local/bin/docker-entrypoint.sh

# Install Python + pip (for build tools)
RUN apk add --no-cache python3 py3-pip

# PEP 668 fix: allow system-wide pip installs in alpine
RUN pip install --no-cache-dir --break-system-packages \
    some-python-package

ENTRYPOINT []
CMD ["node", "src/index.js"]
```

## Debugging Checklist

| Check | Command |
|-------|---------|
| PEP 668 error in build | `grep -r "EXTERNALLY-MANAGED" /usr/lib/python3*/` in build context |
| Base image entrypoint exists | `docker run --rm <image> cat /usr/local/bin/docker-entrypoint.sh` |
| Inherited ENTRYPOINT vs CMD | `docker inspect <image> | jq '.[0].Config.Entrypoint, .[0].Config.Cmd'` |
| Container starts correctly | `docker run --rm -it <image> <actual-cmd>` (test full command) |
