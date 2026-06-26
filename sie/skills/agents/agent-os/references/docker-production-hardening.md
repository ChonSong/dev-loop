# Docker Production Hardening — agent-os (2026-05-07)

## What Was Applied

All hardening on top of the base `docker-compose.yml`:

```yaml
services:
  nanobot:
    cpus: 1.0              # MUST be 1.0+ — LLM inference hangs at 0.5 CPU
    mem_limit: 1g
    tmpfs: /tmp:size=64m,mode=755   # temp workspace in RAM
    # read_only: true     # BROKEN — nanobot writes to /opt/data/nanobot

  backend:
    cpus: 1.0
    mem_limit: 1g
    read_only: true
    tmpfs: /tmp:size=32m,mode=755
    volumes:
      - /home/sean/.nanobot:/root/.nanobot:ro  # config must be writable for persist

  postgres:
    cpus: 0.5
    mem_limit: 7.5g
    # No read_only — postgres needs data directory write access

  cloudflared:
    cpus: 0.25
    mem_limit: 1g

  webhook-emitter:
    cpus: 0.1
    mem_limit: 256m
    read_only: true
    tmpfs: /tmp:size=32m,mode=755
    healthcheck:
      test: ["CMD", "curl", "-sf", "http://backend:3001/api/db/health"]
```

## Key Rules

### CPU: nanobot MUST be ≥1.0

At `cpus: 0.5`, nanobot's `/v1/chat/completions` hangs indefinitely (LLM inference needs CPU headroom). At `cpus: 1.0`, response returns in ~2s.

### Never `read_only: true` for nanobot

Nanobot writes to `/opt/data/nanobot` workspace. `read_only: true` causes immediate restart loop:
```
panic: open /opt/data/nanobot/sessions/sessions.db: read-only file system
```

### webhook-emitter CAN be `read_only: true`

The Go webhook emitter only needs `/tmp` for temporary state. It does NOT need persistent filesystem access. Add `tmpfs` to cover its temp needs:
```yaml
read_only: true
tmpfs: /tmp:size=32m,mode=755
```

### DATABASE_URL password masking

Docker **masks passwords in URLs** in `docker inspect` output and logs — it replaces the password substring with `***`. This is cosmetic (Docker's own redaction), NOT actual corruption. The actual password in the file is unaffected.

**HOWEVER**: When `grep`ping `docker-compose.yml` on the host, the shell may also glob `***` as a file glob pattern, making it appear like the file itself was corrupted. Always verify with Python:
```python
c = open('/home/sean/.hermes/agent-os/docker-compose.yml').read()
import re
m = re.search(r'postgresql://agentos:([^@]+)@postgres', c)
print(repr(m.group(1)))  # prints actual password
```

### SSH timeout: disk-heavy operations

`docker system prune -af` hangs indefinitely on constrained I/O (times out after 35s). Use staged cleanup:
```bash
docker image prune -f          # fast, reclaimable dangling images
docker builder prune -af       # build cache
docker volume prune -f         # unused volumes
```
Never run `docker system prune -af` on this server — it will always timeout.

### After editing docker-compose on host

1. Validate: `docker compose -f docker-compose.yml config --quiet && echo VALID`
2. Recreate affected services: `docker compose up -d [service]`
3. Sync to GitHub: `scp ... docker-compose.yml /opt/data/agent-os/docker-compose.yml`
4. Commit from `/opt/data/agent-os`: `git add -A && git commit && git push`
5. Pull on host for next deploy: `git pull origin main`

### Backend Concurrency Hardening

The backend (`express.json`) should have a body size limit to prevent large payload crashes:
```typescript
app.use(express.json({ limit: '1mb' }));
```

The backend also needs elevated HTTP socket capacity for concurrent nanobot calls:
```typescript
import http from 'http';
http.globalAgent.maxSockets = 50;
```

Nanobot CPU: must be ≥1.0 or `/v1/chat/completions` hangs indefinitely. See nanobot section above.
