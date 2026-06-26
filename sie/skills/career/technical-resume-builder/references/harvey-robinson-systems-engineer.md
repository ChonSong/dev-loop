# Harvey Robinson — Worked CV Example

Full worked example of the Junior Systems Engineer CV build session (June 2026).

## The Role
- **Poster:** Harvey Robinson (recruitment agency, not employer)
- **Client:** Unnamed (likely banking/FS based on their other placements)
- **Title:** Junior Systems Engineer (Early Career)
- **Salary:** $105-115k + super
- **Keywords:** automation, scripting, infrastructure, cloud, home lab, curiosity

## CV Content Flow

### Summary
> Junior infrastructure engineer who has been building, breaking, and fixing production systems throughout his degree. Runs a self-hosted multi-container platform with Cloudflare, CI/CD, systemd, and automated evaluation pipelines. Looking for a Systems Engineer role.

### Engineering Philosophy Box
> **Parsimony:** Given multiple models with equivalent accuracy, the simplest is favoured. PAC learning theory, VC dimension, Minimum Description Length — applies to system architecture as much as ML. Less code, fewer dependencies, more testable surfaces.

### Experience 1 — Self-hosted Agent Infrastructure
- Multi-container platform: Docker Compose with 9 containers, health cascades (depends_on: service_healthy), read-only + tmpfs security on sidecars, Cloudflare Tunnel (17 ingress rules, Access policies, Terraform DNS)
- Multi-language monorepo (Go + Python + TypeScript) with dual orchestrators (Nx + Turbo + uv); CI/CD via GitHub Actions matrix builds
- Systemd with security hardening (NoNewPrivileges, ProtectSystem=strict); automated cron workflows; PostgreSQL backup 269 MB → 94 MB compressed
- Eval-driven pipeline: promptfoo for adversarial LLM-as-judge testing across OWASP LLM categories, 5 evasion strategies, cost/latency thresholds with CI gating
- Custom telemetry server exposing Prometheus-format CPU, memory, and service metrics

### Experience 2 — CasaOS Webhook Emitter (Go)
- Go service subscribing to MessageBus events via WebSocket (nhooyr.io/websocket), fanning out as HMAC-SHA256 signed webhooks with retry backoff [1s, 5s, 30s] and dead-letter queue (JSONL)
- Semaphore concurrency control (buffered chan, MaxConcurrent=10), rate limiting (60/min), ring buffer delivery history (1000 entries) — hand-rolled
- Systemd-managed with Gorilla Mux REST API for dynamic webhook registration; JSON file-backed registry with RWMutex thread safety

### Experience 3 — OneTag HMAS Sydney (Contract)
- Restored 2.45 GB SQL Server backup into Dockerised Linux container (RESTORE WITH MOVE cross-platform migration); ETL pipeline via docker exec + sqlcmd + Python to SQLite
- Cloudflare-authenticated proxy for app delivery behind Docker + Cloudflare Tunnel

### Experience 4 — Autonomous Development Pipeline
- Tick-based autonomous dev: Player agent (2-hourly) implements features against AGENTS.md manifests; Coach agent (4-hourly) reviews commits with evidence gates and rubber-stamp prevention
- Per-repo checkpoint.json + global master-checkpoint tracking priorities and SHAs; 16+ cron jobs orchestrate the pipeline

## Excluded
- casaos-agent, hermes-sync (user request)
- GTO Wizard, all ML/DS projects (not relevant for infrastructure role)
