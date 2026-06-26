# Source Code Deep-Dive — Technical Details for CV Bullets

Extracted from actual source code in `/home/sc/repos/` during the June 2026 Harvey Robinson Systems Engineer CV build. These are concrete, verifiable technical specifics that differentiate Sean's CV from generic graduates.

## agent-os (multi-language monorepo)

### Docker / Infra
- Multi-stage Docker build (3 stages: ts-build, go-build, slim runtime)
- Base images: `node:22`, `golang:1.23-alpine`, `node:22-slim`
- Docker Compose with 4 services: backend (1g mem, 1.0 cpu), postgres 16-alpine (7.5g mem), cloudflared:2026.3.0 (1g mem), webhook-emitter (256m, read_only, tmpfs /tmp:size=32m)
- HEALTHCHECK: `curl -sf http://localhost:3001/api/db/health`, 30s interval, 10s timeout, 3 retries
- Network: custom bridge `agent-net`
- Volume mounts: Docker socket (`/var/run/docker.sock:rw`), Hermes config, full home mount
- Depends_on with `service_healthy` condition (cascading health through stack)

### Backend Stack
- Express ^4.18.2, Socket.IO ^4.7.2, dockerode ^4.0.2, pg ^8.11.3, cors ^2.8.5
- 75+ routes in single index.ts (94KB)
- 22 SPA pages: Dashboard, Chat (SSE), Containers (real-time stats), Terminal (xterm.js PTY), Sessions, Memory, Files, Cron, etc.
- 11 CSS themes including Warm Bento, Matrix, Claude variants

### Monorepo Tooling
- Nx (nx.json with nx-go plugin), Turbo (turbo.json), uv (uv.lock 681KB)
- npm v10.9.2 workspaces
- semantic-release (.releaserc)
- Terraform for Cloudflare IaC (infra/terraform/main.tf)
- 8 PostgreSQL migrations
- Nginx reverse proxy config

## casaos-webhook-emitter (Go event sidecar)

### Dependencies
- `github.com/gorilla/mux` v1.8.1 — HTTP routing
- `nhooyr.io/websocket` v1.8.10 — WebSocket client
- `github.com/google/uuid` v1.6.0 — webhook ID generation
- `gopkg.in/yaml.v3` v3.0.1 — YAML config parsing

### Architecture
- Clean dependency injection: config → registry → engine → bus client → API server
- Two goroutines: client.Subscribe + apiServer.Start
- Graceful shutdown via SIGINT/SIGTERM → context cancel

### Delivery Engine
- Semaphore-based concurrency: `chan struct{}` with MaxConcurrent=10
- HTTP client: `http.Client{Timeout: 10s}`
- Retry backoff: [1s, 5s, 30s] (3 attempts)
- HTTP 410 handling (permanent failure, no retry)
- Dead-letter queue: JSONL file at `~/.local/share/casaos-agent/webhook-emitter/failed_deliveries.jsonl`
- Ring buffer: last 1000 results in-memory for delivery history endpoint
- HMAC signing: `X-CasaOS-Signature: HMAC-SHA256(webhook.Secret, body)`

### Request Headers
```
Content-Type: application/json
X-CasaOS-Event: <webhook-id>
X-CasaOS-Timestamp: <RFC3339>
X-CasaOS-Delivery-ID: <event-uuid>
X-CasaOS-Signature: <HMAC-SHA256>
```

### REST API (Gorilla Mux)
- GET /webhooks, POST /webhooks (wh_ + 12-char UUID), DELETE /webhooks/{id}
- GET /webhooks/{id}/deliveries, POST /webhooks/{id}/test
- GET /health → `{"status":"healthy","service":"casaos-webhook-emitter"}`
- GET /metrics → `exporter_up 1`

### Config
- Default listen: localhost:9393
- MaxConcurrent: 10, DeliveryTimeout: 10s, Retry: 3, RateLimit: 60/min
- Default base URL: http://localhost:8080
- 30s ping ticker keepalive on WebSocket
- JSON file-backed webhook registry with sync.RWMutex

### Build
- Makefile with cross-compile: GOOS=linux GOARCH=amd64+arm64, GOOS=darwin

## energy-aware-task-router (Python carbon-aware scheduler)

### Architecture
- 8 Python modules: api.py, router.py, carbon.py, config.py, audit.py, queue.py, cli.py, monitoring.py
- FastAPI >=0.110, uvicorn >=0.27, httpx >=0.27, pydantic >=2.6, structlog >=24.1, redis >=5.0, typer >=0.9
- Dockerfile: python:3.12-slim, EXPOSE 8009
- docker-compose: app + redis:7-alpine (port 6380)

### Systemd Unit
- Security hardening: NoNewPrivileges=true, ProtectSystem=strict, PrivateTmp=true
- ReadWritePaths scoped, After=network-online.target redis.service

### CI/CD (GitHub Actions)
- Matrix: Python 3.11 + 3.12
- Service container: redis:7-alpine with health check (redis-cli ping, 10s interval, 5 retries)
- Steps: ruff check → ruff format --check → pytest tests/ -v --timeout=30

### Routing Logic
- GridCarbonLevel: LOW (<200) ↔ MEDIUM (200-450) ↔ HIGH (>450) ↔ UNKNOWN gCO₂/kWh
- Cache: in-memory dict, 300s TTL
- Fallback chain: cached → missing key → UNKNOWN → API failure → UNKNOWN
- Fail-open design (dead tasks worse than suboptimal routing)
- ISO 8601 duration parsing for deferral config (PT24H default)

### Audit Trail (SQLite)
- Table: routing_decisions (id, task_id, decision, carbon_level, intensity, region, reason, timestamp)
- Redis sorted-set for deferral queue (key: deferred:tasks, score: Unix timestamp)

## promptfoo Configuration

### Config Files
- `/home/sc/repos/llm-benchmark-platform/promptfooconfig.yaml` — 3 test cases with llm-rubric, contains, cost, and latency assertions
- `/home/sc/repos/llm-benchmark-platform/redteam.yaml` — OWASP LLM plugins (01, 02, 06), jailbreak, PII extraction, harmful content
- 5 evasion strategies: basic, base64, jailbreak, leetspeak, rot13
- Pass threshold: 0.75 (redteam), 0.8 (extended)
- Providers: deepseek-v4-flash, gpt-5.4

## Coach/Player Autonomous Dev Pipeline

### Player Agent
- Runs every 2 hours via cron
- Model: deepseek-v4-flash
- Flow: Read checkpoint → Find project → Investigate → Implement → Test → Commit → Update checkpoint
- Time budgets: 60s investigation, 180s implementation, 180s test, 300s build (500s total hard limit)
- Max 2 consecutive ticks on same project (round-robin)

### Coach Agent
- Runs every 4 hours via cron
- Model: openrouter/owl-alpha (stronger, free, 1M context)
- Flow: Read checkpoint → Read diff → Run tests → Verify AGENTS.md criteria with evidence → Output DECISION
- Five rubber-stamp prevention mechanisms
- Fresh context per run (separate session from Player)

### State
- `~/.hermes/master-checkpoint.json` — global state (active_project, priority, health scores, SHAs)
- Per-project `.checkpoint.json` — task progress, completed tasks, blocker flags
- Per-project `AGENTS.md` — task manifests with success criteria, coach checks, skills
