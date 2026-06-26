# hermes-sync Local Build: Patterns & Pitfalls

Session-validated patterns for `~/hermes-sync/scripts/sync-and-push.sh` and its Dockerfile.

## Build context strategy

The script rsyncs hermes-agent into `hermes-sync/hermes-agent/` before building. The Dockerfile then copies from there. This avoids `--build-context` relative path resolution failures in Docker 29.1.3.

**rsync excludes** (validated):
```
--exclude='.git'
--exclude='node_modules'
--exclude='web/node_modules'
--exclude='ui-tui/node_modules'
--exclude='web/dist'
--exclude='ui-tui/dist'
--exclude='__pycache__'
--exclude='*.pyc'
--exclude='.env'
--exclude='*.log'
--exclude='*.tmp'
```

## Dockerfile npm patterns

### `--prefix` over `cd`
```dockerfile
# WRONG — web/ doesn't exist at this layer (COPY happens after npm install)
RUN cd web && npm install

# RIGHT — npm --prefix resolves paths relative to WORKDIR
RUN npm install --prefix web
RUN npm run build --prefix web
```

### Scoped package must pre-create parent dir
```dockerfile
# WRONG — cp fails because node_modules/@hermes/ doesn't exist
COPY ui-tui/packages/hermes-ink node_modules/@hermes/ink

# RIGHT
RUN mkdir -p node_modules/@hermes
COPY ui-tui/packages/hermes-ink node_modules/@hermes/ink
```

### COPY dest trailing slash preserves directory structure
```dockerfile
# WRONG — hermes-agent/web becomes ./web (flattened)
COPY hermes-agent/web ./web

# RIGHT — hermes-agent/web becomes ./web (structure preserved)
COPY hermes-agent/web ./web/
```

### Entrypoint needs explicit chmod
```dockerfile
# WRONG — results in exit 126 (permission denied)
COPY docker/entrypoint.sh /entrypoint.sh

# RIGHT
COPY --chmod=0755 docker/entrypoint.sh /entrypoint.sh
```

### Do NOT validate ink bundle with node -e import
```dockerfile
# WRONG — fails because ink-bundle.js imports 'react' which was stripped in production install
RUN node --input-type=module -e "await import('@hermes/ink')"
```
This produces: `ERR_MODULE_NOT_FOUND: Cannot find package 'react'`. The bundled ink works without this validation step.

## Layer-cached npm install technique

Copy `package.json` + `package-lock.json` separately first, run `npm install`, then copy source:
```dockerfile
# Root deps
COPY hermes-agent/package.json hermes-agent/package-lock.json ./
RUN npm install

# Web deps (separate layer — only invalidates when web/package.json changes)
COPY hermes-agent/web/package.json hermes-agent/web/package-lock.json hermes-agent/web/
RUN npm install --prefix hermes-agent/web

# UI-TUI deps
COPY hermes-agent/ui-tui/package.json hermes-agent/ui-tui/package-lock.json hermes-agent/ui-tui/
RUN npm install --prefix hermes-agent/ui-tui

# hermes-ink (scoped package deps)
COPY hermes-agent/ui-tui/packages/hermes-ink/package.json hermes-agent/ui-tui/packages/hermes-ink/
RUN npm install --prefix hermes-agent/ui-tui/packages/hermes-ink

# Now copy full source
COPY hermes-agent/ ./
```

## Container naming conflict on rolling restart

`docker-compose.yml` uses bare container names (`hermes`, `hermes-dashboard`) without a project prefix. After `docker rm -f hermes`, `docker start hermes` creates a bare-name container that docker-compose may not track.

**Safe rolling restart sequence:**
```bash
docker rm -f hermes
docker start hermes
docker restart hermes-dashboard  # use restart, not rm+start (avoids name conflict)
```

**Alternative** (if compose project naming is used):
```bash
docker compose -f docker/docker-compose.yml up -d --no-deps
```

## Disk space facts (measured)

- Host disk: ~461GB `/dev/sda2`
- Prune freed: ~37-80GB in a single pass
- Single npm install + uv pip install can fill disk again
- Docker builder cache (`docker builder prune -af`) is the main consumer
- After prune + rebuild, another prune may be needed before the build completes

## Image digest reference

Latest successful build: `ghcr.io/chonsong/hermes-sync@sha256:6fb6b47d865897e58294dc2d2f1807ebe379bb61a08512fa834b880cb5cfc508`

## Known non-fatal warnings

- `FromPlatformFlagConstDisallowed` — FROM statements use `--platform=linux/amd64` with a constant value. This is expected and harmless.
