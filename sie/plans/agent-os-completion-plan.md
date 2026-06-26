# agent-os Completion Plan

## Context

agent-os monorepo at `~/agent-os/` (GitHub: ChonSong/agent-os) is ~80% scaffolded.
The core agent-os stack (everything-dashboard + nanobot + MiniMax) is live and working.
CI runs but "Build and Push Agent OS" workflow is broken (deploy step is a TODO).
Go packages are just `go.mod` stubs. PostgreSQL schema and Cloudflare infra are spec-only.

---

## Phase 1 — Fix Deploy Pipeline (Critical)

**Goal**: Get CI "Build and Push Agent OS" passing and a real Docker image published to ghcr.io/ChonSong/agent-os.

### 1.1 Create `docker-bake.hcl`
Define multi-stage bake file for the unified agent-os image.
The image should include:
- nanobot serve on port 8900
- everything-dashboard backend on port 3001
- Dashboard frontend (built static assets served by backend)
- Environment variable config for MiniMax API key

### 1.2 Fix `deploy.yml`
Replace the TODO comment with real `docker buildx bake -f docker-bake.hcl --push`.
Include:
- QEMU for multi-arch (arm64 + amd64)
- `ghcr.io/ChonSong/agent-os` image with tags `latest` and `${github.sha}`
- Proper cache-from/cache-to for build speed

### 1.3 Update `docker-compose.yml` (production variant)
Create `docker-compose.prod.yml` that:
- Pulls from `ghcr.io/ChonSong/agent-os:latest`
- Has correct port exposures (8900, 3001, 9119)
- Uses env vars for API keys instead of hardcoding

### 1.4 Verify CI green
Trigger a manual dispatch or push a no-op commit to verify the build passes.

---

## Phase 2 — E2E Integration Verification (High)

**Goal**: Verify the full chain works and document any gaps.

### 2.1 Dashboard → nanobot → MiniMax E2E test
Write and run a test script that:
1. Hits `localhost:3001/api/agent/chat` with a test prompt
2. Confirms it proxies to nanobot on :8001
3. Confirms nanobot responds (check nanobot logs for MiniMax API call)
4. Reports any failures

### 2.2 Fix dashboard backend routing
Check if the Express backend at :3001 correctly routes `/api/agent/*` to nanobot :8001.
Fix any missing routes or broken socket.io config.

### 2.3 Agent-core Python sidecar
The `apps/dashboard/agent-core/` directory exists — verify it has the nanobot wrapper script.
If missing, create the entrypoint that launches nanobot as a subprocess.

---

## Phase 3 — PostgreSQL Schema (High)

**Goal**: Apply the schema from SPEC.md to Neon PostgreSQL.

### 3.1 Create migration scripts
In `infra/postgres/migrations/`, create SQL migration files:
- `001_initial_schema.sql` — creates all tables from SPEC.md
- `002_...` for subsequent changes

### 3.2 Set up Neon connection
Store Neon connection string in GitHub Actions secrets (`NEON_CONNECTION_STRING`).
Add a migration job to CI that runs after release.

### 3.3 Verify schema
Run migrations against Neon dev database and verify tables exist.

---

## Phase 4 — CasaOS Go Agent + Webhook Emitter (Medium)

**Goal**: Replace `go.mod` stubs with real implementations.

### 4.1 `infra/CasaOS/agent` — Go CLI
Implement the CasaOS CLI wrapper that:
- Connects to CasaOS via Unix socket or HTTP API
- Lists running containers
- Can start/stop/remove containers on command
- Exposes a clean CLI interface

### 4.2 `infra/CasaOS/webhook-emitter` — Go sidecar
Implement the webhook emitter that:
- Connects to CasaOS MessageBus (or polls)
- Emits container lifecycle events as HTTP POST webhooks
- Configurable webhook URL + auth headers

### 4.3 Add Go to CI
Ensure `go build ./...` and `go test ./...` pass in CI.

---

## Phase 5 — Cloudflare Infrastructure (Medium)

**Goal**: Terraform-managed tunnel + Access policy.

### 5.1 `infra/terraform/`
Create Terraform files for:
- `cloudflared` tunnel (or use existing tunnel)
- Cloudflare Access policy with GitHub OAuth provider
- DNS records for `appexample.codeovertcp.com`

### 5.2 State management
Store Terraform state in a GCS bucket or Cloudflare's API.
**Important**: Do NOT commit any secrets to git.

### 5.3 Document DNS/tunnel details
Write connection info to a secure note in the project.

---

## Phase 6 — CI Quality Gates (Medium)

**Goal**: Make CI meaningful, not just "passing".

### 6.1 Enforce linting
- Python: `ruff check packages/` must pass (not `|| true`)
- TypeScript: `turbo lint` must pass
- Go: `go vet ./...` must pass

### 6.2 Test coverage gate
Set a minimum coverage threshold (e.g., 70%) for Python packages.

### 6.3 Path-filtered CI improvements
Ensure only changed packages are tested (already partially working).

---

## Execution Order

```
Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6
  ↑           ↑         ↑         ↑         ↑
  |           |         |         |         +-- can run parallel to others
  |           |         |         +-- Go work after Phase 1 (CI will fail until then)
  |           |         +-- can start after Phase 2 (needs backend stable)
  |           +-- E2E test after Phase 1 (needs working image)
  +-- Must be first (CI broken = everything blocked)
```

---

## Cron Job Roster

| Phase | Job name | Trigger | Skills |
|-------|----------|---------|--------|
| Phase 1 | agent-os: Phase 1 — Deploy pipeline fix | Immediately | github-pr-workflow, hermes-docker-workflow |
| Phase 2 | agent-os: Phase 2 — E2E verification | After Phase 1 completes | nanobot-integration-plan |
| Phase 3 | agent-os: Phase 3 — PostgreSQL migrations | After Phase 2 | multi-provider-api-calls |
| Phase 4 | agent-os: Phase 4 — CasaOS Go impl | After Phase 3 | (none — pure Go) |
| Phase 5 | agent-os: Phase 5 — Cloudflare TF | After Phase 4 | (none — terraform) |
| Phase 6 | agent-os: Phase 6 — CI quality gates | After Phase 5 | github-pr-workflow |
