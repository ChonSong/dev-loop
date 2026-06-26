# HWC QA — hermes-web-computer Deployment Audit

System overview: **hermes-web-computer** is a Go backend + Svelte 5 frontend + WebSocket JSON-RPC multiplexer, served on port 3005 via systemd (`hwc-server.service`, `Restart=always`).

## Service Endpoints

| Endpoint | Type | Expected |
|----------|------|----------|
| `GET /health` | Health check | `"ok"` (string body, HTTP 200) |
| `GET /` | SPA | `<title>Hermes Web Computer</title>` |
| `GET /ws` | WebSocket | JSON-RPC multiplexer (3 protocols: ui/agent/audio) |
| `GET /api/system/metrics` | Host telemetry | JSON: cpu%, memory, network, wifi, battery, volume, temp, audio |

## QA Checklist (execute in order)

### 1. Health Check

```bash
curl -s http://localhost:3005/health
# Expected: "ok"
# Response time should be < 100ms
```

### 2. SPA Title Verification

```bash
curl -s http://localhost:3005/ | grep -o '<title>[^<]*</title>'
# Expected: "<title>Hermes Web Computer</title>"
```

Title is the definitive fingerprint — if wrong, wrong app is deployed.

### 3. Binary Freshness (Host-vs-Container Gap)

The HWC binary runs on the **host** via systemd. Inside the Hermes container, the host's PID namespace is **not** shared — `lsof`, `ss`, and `/proc` won't show the host process. Freshness must be inferred from synced binary copies.

**Binary copies and what they mean:**

| Path | Purpose |
|------|---------|
| `/opt/data/hwc-server` | Synced copy from host (most recent sync) |
| `/opt/data/home/hwc-server` | Alternative sync from host home dir |
| `/opt/data/hermes-web-computer-state/hwc-server` | State checkpoint copy |
| `/opt/data/cache/hermes-web-computer/hermes-web-sync/bin/hwc-server` | Cached from git sync |
| `/tmp/hwc-server` | Legacy/temp binary (may be stale) |

**Freshness check:**

```bash
# 1. Check the newest binary copy
stat --format='%y %s %n' /opt/data/hwc-server /opt/data/home/hwc-server

# 2. Check the most recent git commit from the cached repo
cd /opt/data/cache/hermes-web-computer/hermes-web-sync && git log -1 --format="%h %ai %s"

# 3. Compare
```
- If binary stat date > git commit date: host built from uncommitted changes (or rebuild without code change)
- If binary stat date < git commit date: stale binary, needs rebuild
- If binary stat date ≈ git commit date: fresh build matching committed code

### 4. Frontend Build Staleness

The Svelte 5 SPA is embedded in the Go binary. Frontend asset hashes reveal whether the served build matches the cached one:

```bash
# Served assets (from running server)
curl -s http://localhost:3005/ | grep -o 'src="/assets/[^"]*\.js"' | head -5

# Cached assets (from git sync)  
ls /opt/data/cache/hermes-web-computer/hermes-web-sync/frontend/dist/assets/index-*.js 2>/dev/null
```

**Differing hashes = frontend was rebuilt independently of git.** Check:
- Are the served hashes newer than the cached ones? (frontend was rebuilt on host)
- Are the binary dates older than the frontend build? (only frontend changed, not backend)
- Check `Last-Modified` headers on the assets for precise timestamps:

```bash
curl -sI http://localhost:3005/assets/index-*.js | grep -i last-modified
```

### 5. System Metrics Verification

```bash
curl -s http://localhost:3005/api/system/metrics
# Returns JSON with cpu, memory, network, wifi, battery, volume, temperature, audio
```

Confirm: real host data is being served (not default/stale values). Battery and wifi presence confirm live host connectivity.

## Known Binary Locations (Host)

The actual binary run by systemd lives at a host path not directly visible from the container. Based on the project's AGENTS.md and deploy scripts, the host build flow is:

```
/home/sean/.hermes/hermes-web-computer/backend/
  ├── cmd/server/       # Main package (go build -o ...)
  └── go build -o /tmp/hwc-server ./cmd/server/
```

The binary that gets synced back to the container is picked up from wherever `hermes-web-sync` copies it.

## Interpretation Guide

| Gap Pattern | Interpretation |
|-------------|----------------|
| Git = May 26, Binary = Jun 8, Frontend = Jun 10 | Active development ongoing. Host-side builds not committed. Frontend rebuilt 2 days ago; backend rebuilt 4 days earlier. Git repo is stale. |
| Git = May 26, Binary = May 28, Frontend = May 26 | Normal: binary rebuilt from same git tree (maybe different target). No uncommitted frontend changes. |
| Git = May 26, Binary = May 26, Frontend = May 26 | In sync: all artifacts match the last commit. |
| Binary stat = exact git commit timestamp | Clean rebuild from committed code. |
| All dates identical across all artifacts | State of the system is consistent and aligned with git. |

## Pitfalls

- **Host PID invisible from container.** With `network_mode: host`, the network namespace is shared but PID namespace is separate. You cannot `lsof -i :3005` and get the binary path. Rely on stat dates and asset hashes for inference.
- **Multiple binary copies diverge.** You may find 3-5 copies of `hwc-server` with different dates across `/opt/data`. The newest one is the most recently synced from the host.
- **System vs state binary.** The `/opt/data/hermes-web-computer-state/hwc-server` copy is a checkpoint, not necessarily the current running binary.
- **Frontend build without Go rebuild is valid.** The Svelte SPA can be rebuilt independently — only asset files change, the Go binary stays the same. The running server serves the new assets from disk.
- **No `-ldflags` build info.** The Go binaries don't embed git commit hashes. Adding `-ldflags="-X main.Commit=$(git rev-parse HEAD)"` would make freshness deterministic.
