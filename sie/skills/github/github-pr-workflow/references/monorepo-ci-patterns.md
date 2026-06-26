# Monorepo CI Patterns (ChonSong/agent-os)

Patterns for diagnosing and fixing CI failures in this multi-service monorepo.

## Architecture

```
agent-os/
├── dashboard/          # Node.js/TypeScript frontend
├── nanobot/            # Python API service
├── workflows/          # Go service
├── observability/      # Python monitoring
├── docker-compose.yml  # Dev orchestration
├── Dockerfile.nanobot
├── Dockerfile.dashboard
└── .github/workflows/
    ├── ci.yml          # lint + test all packages
    ├── build-and-deploy.yml  # Docker image push
    └── release.yml      # semantic-release
```

## Common Failure Patterns

### 1. `|| true` Guard Clauses (MOST COMMON)

**Signatures in CI:**
```yaml
# WRONG — hides failures
- run: npm run lint || true
- run: ruff check . || true
- run: mypy . || true
- run: go test ./... || true

# CORRECT — let CI fail
- run: npm run lint
- run: ruff check .
- run: mypy .
- run: go test ./...
```

**Detection:**
```bash
grep -rn '|| true' .github/workflows/
```

**Why it happens:** Developers add `|| true` to "temporarily" suppress failures during development, then forget to remove it. The CI badge stays green and real errors are invisible.

**The fix loop:**
1. Remove `|| true` from the failing step
2. Run CI to see the real error
3. Fix the real error
4. Commit

### 2. Missing `tsconfig.json` (TypeScript)

**Symptom:** `tsc --noEmit` fails without useful error message.

**Cause:** `dashboard/` didn't have its own `tsconfig.json` — it inherited from root which had `references` to non-existent projects.

**Fix:** Add `dashboard/tsconfig.json`:
```json
{
  "extends": "../tsconfig.json",
  "compilerOptions": {
    "outDir": "../dist/dashboard",
    "rootDir": "src"
  },
  "include": ["src/**/*"]
}
```

**Verification:** `cd dashboard && npx tsc --noEmit`

### 3. Go Package With No Test Files

**Symptom:**
```
go: cannot run tests defined in packages that list no test files
```

**Cause:** `workflows/` package had no `*_test.go` files but `go test ./...` was run in CI.

**Fix:** Add a stub test:
```go
package workflows

import "testing"

func TestStub(t *testing.T) {
    // Placeholder — add real tests
}
```

### 4. NanobotAdapter Default Port Wrong

**Symptom:** Backend connects to port `8001` but nanobot listens on `8900`.

**Cause:** `NanobotAdapter.__init__` had hardcoded `default_port = 8001` but nanobot's actual default is `8900`.

**Fix in adapter:**
```python
default_port: int = 8900  # nanobot default
```

**Verification:** Check nanobot source for its actual default port.

### 5. Missing `.releaserc`

**Symptom:** Release workflow fails with `No configuration found.`

**Cause:** semantic-release needs explicit config — no default.

**Fix:** Create `.releaserc`:
```json
{
  "branches": ["main"],
  "plugins": [
    "@semantic-release/commit-analyzer",
    "@semantic-release/release-notes-generator",
    "@semantic-release/github"
  ]
}
```

### 6. Dockerfile CMD Wrong Binary Name

**Symptom:** Container starts and exits immediately.

**Cause:** `CMD ["dashboard"]` but the actual binary is built as `agent-os-dashboard` or similar.

**Fix:** Run `docker build`, check the binary name with `docker run --rm image ls /app/` or look at the build output.

### 7. Deploy Workflow Has Empty `run:` Block

**Symptom:** Deploy step does nothing.

**Cause:** Workflow had a TODO comment instead of actual deployment steps:
```yaml
# WRONG
- name: Deploy
  run: |
    # TODO: implement deployment

# CORRECT
- name: Deploy
  run: |
    kubectl rollout restart deployment/agent-os -n production
```

## Diagnostic Commands

```bash
# Find all || true in workflows
grep -rn '|| true' .github/workflows/

# Run all CI checks locally (from repo root)
npm install && cd dashboard && npm install && npx tsc --noEmit && cd ..
pip install -e nanobot[api] && ruff check nanobot observability
cd workflows && go test ./...

# Check Docker build
docker buildx build --platform linux/amd64 \
  --tag "ghcr.io/chonsong/agent-os:$(git rev-parse HEAD::1 | cut -c1-8)" \
  --file ./Dockerfile.nanobot \
  --push \
  .

# Verify semantic-release config
npx semantic-release --dry-run
```

## Key Files and Their CI Roles

| File | CI Trigger | Job |
|------|-----------|-----|
| `dashboard/src/**` | push to `dashboard/` | lint, typecheck |
| `nanobot/**/*.py` | push to `nanobot/` | ruff, mypy |
| `observability/**/*.py` | push to `observability/` | ruff, mypy |
| `workflows/**/*.go` | push to `workflows/` | go test |
| `Dockerfile.nanobot` | push to `Dockerfile.nanobot` | build-and-deploy |
| `Dockerfile.dashboard` | push to `Dockerfile.dashboard` | build-and-deploy |
| `.releaserc` | push to `main` | release |
