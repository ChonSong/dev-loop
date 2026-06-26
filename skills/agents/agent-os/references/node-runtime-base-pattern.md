# Dockerfile Runtime Base Pattern: node:22-slim

## Problem

Multi-stage Docker builds for Node.js projects often use a minimal base (like `debian:slim` or `alpine`) for the runtime stage to reduce image size. However, copying the Node.js binary from the build stage is fragile:

1. The binary path may change between base image versions
2. `npm` and `corepack` are symlinks into `/usr/local/lib/node_modules/` — copying them without the target files produces dangling links
3. The node binary is dynamically linked and requires glibc and other shared libraries

## Failed Approach (debian:13-slim + copy)

```dockerfile
FROM debian:13-slim
COPY --from=ts-build /usr/local/bin/node /usr/local/bin/node
COPY --from=ts-build /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -sf ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm
```

This broke when the `node:22` base image was updated — the COPY would silently fail or the binary wouldn't work due to missing libraries.

## Working Approach (node:22-slim)

```dockerfile
FROM node:22-slim
# Node.js v22.x is already at /usr/local/bin/node
# npm and corepack are already set up
# glibc and all shared libraries are included
```

## Docker CLI Installation

The `docker-cli` apt package name varies across Debian versions. Use the official static binary:

```dockerfile
RUN curl -fsSL https://download.docker.com/linux/static/stable/x86_64/docker-27.5.1.tgz | \
    tar xz --strip-components=1 -C /usr/local/bin docker/docker
```

## Image Size Comparison

- `node:22-slim`: ~200MB (includes Node.js, npm, glibc)
- `debian:13-slim` + copied node: ~250MB (larger due to copying node_modules)
- `node:22` (full): ~1GB (includes build tools, not needed for runtime)

## When to Use Each

| Base Image | Use Case |
|------------|----------|
| `node:22-slim` | Runtime stage for Node.js apps (recommended) |
| `node:22-alpine` | Even smaller runtime (~150MB), but Alpine musl may cause native module issues |
| `node:22` (full) | Build stage only (includes gcc, make, etc.) |
| `debian:slim` | Non-Node runtime stages (Go, Python with custom builds) |

## History

| Date | Change | Reason |
|------|--------|--------|
| Pre-2026-05-09 | `COPY --from=ts-build /usr/local/bin/node` | Original approach |
| 2026-05-09 | Added `COPY --from=ts-build /usr/local/lib/node_modules` + symlinks | npm/corepack symlinks broken |
| 2026-05-10 | Switched to `FROM node:22-slim` | Node binary disappeared from ts-build stage after image update |
