# host.docker.internal — Docker-to-Host Networking Pattern

## Problem
Backend runs in Docker but needs to reach a service on the host (Hermes Agent on port 8642). Docker Compose service names only resolve within the compose network.

## Solution
Use `host.docker.internal` with the Docker gateway:

### docker-compose.yml
```yaml
services:
  backend:
    extra_hosts:
      - "host.docker.internal:host-gateway"
    environment:
      - HERMES_API_URL=http://host.docker.internal:8642
```

### docker run
```bash
docker run -d \
  --add-host host.docker.internal:host-gateway \
  -e HERMES_API_URL=http://host.docker.internal:8642 \
  ...
```

## Why not just use the host IP?
- Host IP can change (DHCP, laptop moves between networks)
- `host-gateway` resolves to the Docker bridge gateway, which is always reachable from containers
- Works on Linux (unlike `host.docker.internal` which is macOS/Windows only by default — `host-gateway` makes it work on Linux too)

## Alternative: network_mode: host
If the container needs full host network access, use `network_mode: host`. But this removes network isolation and prevents inter-container DNS resolution. The `host.docker.internal` pattern is more surgical.

## Why not put Hermes in docker-compose?
Hermes is the host's own agent (this Hermes container). It uses `network_mode: host` and binds 8642/9119. Adding a second Hermes service to compose would cause port conflicts. The host already runs Hermes — just connect to it.
