---
name: hwc-backend-integration
description: "Hermes Web Computer backend integration — Hermes gateway API, SSE streaming, tool execution, server deployment, and container-host binary management."
category: "devops"
tags: ["hermes-web-computer", "hwc", "hermes-agent", "go", "sse", "streaming"]
---

# HWC Backend Integration

Hermes Web Computer (HWC) backend integration patterns — connecting the Go backend to the Hermes Agent gateway, SSE streaming, tool execution, and deploying the server binary from container to host.

## When to Activate

- Wiring HWC backend to Hermes Agent (chat, tool execution, streaming)
- Debugging HWC-Hermes connectivity issues
- Deploying updated HWC binary to EndeavourOS host
- Understanding Hermes gateway API shape
- Setting up container-host build/deploy workflows

## Hermes Gateway API

### Endpoint Map

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | HTML dashboard (SPA shell) |
| `/api/sessions` | GET | List all sessions |
| `/api/chat/start` | POST | Start streaming conversation (returns `stream_id`) |
| `/health` | GET | Health check — returns `"ok"` |
| `/ws` | WS | WebSocket JSON-RPC (HWC internal, used by frontend) |

### Port Map

| Service | Host Port | Container | Notes |
|---------|-----------|-----------|-------|
| Hermes Gateway | `8787` | `hermes-webui-hermes-webui-1` | Mapped to `0.0.0.0:8787` on host |
| HWC Server | `3005` | runs on host directly | `agent-os server` binary |
| Hermes Container | `5357` | `hermes` (unhealthy) | Internal only, not gateway |
| Legacy Tunnel | `3113` | — | Old cloudflared port, may conflict |

**Key pitfall**: Old HWC code defaults to `localhost:8642` — this port does NOT exist. Always use `8787`.

### Session-Based Streaming

`/api/chat/start` requires an existing session. Get sessions via `GET /api/sessions`:

```bash
curl -s http://localhost:8787/api/sessions | python3 -c "
import sys, json
d = json.load(sys.stdin)
for s in d['sessions'][:3]:
    print(f\"{s['session_id']} — {s['title']}\")
"
```

Then stream:
```bash
curl -s -X POST http://localhost:8787/api/chat/start \
  -H "Content-Type: application/json" \
  -d '{"session_id":"<id>","message":"Hello"}'
```

Response: `{"stream_id":"...","session_id":"...","turn_id":"...","effective_model_provider":"..."}`

## SSE Streaming Protocol

The `agent/streamer.go` package handles SSE from `/api/chat/start`:

- Reads line-by-line, dispatches on `event:` headers
- Event types: `token`, `reasoning`, `tool_call`, `tool_result`, `stream_end`, `error`
- `tool_call` events carry `id`, `name`, `arguments`
- `tool_result` events carry `result` text

**Event flow**: `stream_start` → multiple `token`/`reasoning` → `tool_call`/`tool_result` → `stream_end`

## Tool Execution Architecture

`handleToolExecute` in `backend/ws/multiplexer.go` uses the same SSE streamer as chat. It sends a prompt like:

```
"Execute tool 'X' with arguments: {...}"
```

And collects `token` and `tool_result` events into the response. Results are sent back via WS as:

```json
{"protocol": "event", "event": "tool.result", "data": {"session_id": "...", "tool_name": "X", "result": "..."}}
```

**Pitfall**: Do NOT use OpenAI `/v1/chat/completions` — the Hermes gateway does not implement this endpoint. Always use `/api/chat/start` SSE.

## Server Deployment

### Building

The HWC binary is built on the host (Go not in container):

```bash
cd /home/sean/.hermes/hermes-web-computer/backend
go build -o /tmp/hwc-server-new ./cmd/server/
```

The `.gopath` directory on the host provides Go tooling. The Makefile has `build` target.

### Deploying (Binary Swap)

**Critical**: Cannot overwrite a running binary — Linux returns "Text file busy":

```bash
# 1. Kill old process (use explicit PID to avoid pgrep issues)
kill <PID>
sleep 2

# 2. Swap binary
cp /tmp/hwc-server-new /home/sean/.hermes/hermes-web-computer/backend/agent-os
chmod +x /home/sean/.hermes/hermes-web-computer/backend/agent-os

# 3. Restart
PORT=3005 HERMES_HWC_ROOT=/home/sean/.hermes/hermes-web-computer \
  nohup ./backend/agent-os server > /tmp/hwc-server.log 2>&1 &
```

**Note**: The `--port` flag does NOT work. Use `PORT=3005` env var instead.

### Verifying

```bash
curl -s http://localhost:3005/health   # Should return "ok"
curl -s http://localhost:3005/ws       # Should return 426 (WebSocket upgrade required — expected)
```

## Container-Host Development Workflow

### Path Map (Updated 2026-06-03)

| Context | Path | Notes |
|---------|------|-------|
| **Cron job container** (this env) | `/opt/data/hermes-web-computer` | Go at `/usr/bin/go`, GOPATH `/opt/data/home/go` |
| **hermes-webui container** | `/home/hermeswebui/.hermes/hermes-web-computer` | Sync/copy from host; may be stale |
| **EndeavourOS host** | `/home/sean/.hermes/hermes-web-computer` | Canonical repo; builds run here |

**Important**: The cron job container CANNOT SSH to the host — the SSH key at `/home/hermes/.ssh/id_ed25519` does not exist. The Docker socket at `/var/run/docker.sock` exists but the process lacks permissions. Health checks that need host access (e.g., checking if the HWC server is running on port 3005) must use `curl http://172.19.0.1:3005` — but this may also be unreachable depending on network topology.

### Health Check Pattern (For Terminal-Available Sessions)

When terminal IS available (not cron mode):

```bash
# From /opt/data/hermes-web-computer:
test -f frontend/dist/index.html && echo "frontend: OK" || echo "frontend: MISSING"
git log --oneline -1
git status --short
curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://172.19.0.1:3005
find e2e -name "*.spec.ts" | wc -l
find backend -name "*.go" | wc -l
find frontend/src/components -name "*.svelte" | wc -l
```

### Editing and Building

When editing from the cron container (where the repo is at `/opt/data/hermes-web-computer`):

1. Edit code in container
2. Build: `GOPATH=/opt/data/home/go go build -o /tmp/hwc-server ./cmd/server/`
3. Test: `GOPATH=/opt/data/home/go HERMES_HWC_ROOT=/opt/data/hermes-web-computer go test ./... -count=1 -timeout=120s`
4. Commit and push from container

**For host builds** (when SSH is available from another container):
1. Build on host: `ssh ... "cd /home/sean/.hermes/hermes-web-computer/backend && go build -o /tmp/hwc-server-new ./cmd/server/"`
2. Kill + swap + restart on host (see above)
3. Verify tests pass on host

**Import management**: When removing code that uses imports, verify the import isn't used elsewhere before removing. `go build` will tell you exactly which imports are unused.

**Git hygiene**: Run `git diff --cached --stat` before committing to ensure only intended files are staged. Playwright cache and `.npm-cache` directories can bloat commits.

## References

- `references/hermes-gateway-sse.md` — Full SSE event flow and session lifecycle
- `references/container-access-patterns.md` — Container topology, what works from cron container, path discovery
- `references/hwc-server-management.md` — Server lifecycle management