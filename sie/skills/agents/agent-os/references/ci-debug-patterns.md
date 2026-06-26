# CI Debugging Pattern Discoveries (2026-05-05)

**Core insight:** In a multi-stage CI pipeline, fixing one failure often reveals the next. Each fix changes the failure surface. Never assume the pipeline is fixed after one commit.

### Real Example from agent-os Session

1. First CI run → mypy failing (import-untyped on yaml/croniter)
2. Fixed mypy → pushed commit → CI ran → mypy passed BUT Python job still failed (pytest collection errors now visible)
3. Fixed pytest collection → CI ran → Python passed BUT CI didn't trigger at all (workflow-only change + pyproject.toml not in tracked paths)
4. Forced CI with trivial tracked-file change → CI ran → all jobs passed

**Lesson:** Check CI completion after EVERY commit. The "final" failure may be several layers deep.

## uv pip install -e Reproduces CI Exactly

When CI and local mypy results diverge, create a fresh uv venv that mirrors CI's install approach:

```bash
uv venv /tmp/ci-test --python 3.11
uv pip install \
  -e /opt/data/agent-os/packages/nanobot \
  -e /opt/data/agent-os/packages/observability \
  -e /opt/data/agent-os/packages/agent-adapter \
  ruff pytest pytest-asyncio pytest-cov mypy \
  --python /tmp/ci-test
/tmp/ci-test/bin/python -m mypy packages/ --config-file=pyproject.toml --follow-imports=skip
```

**Why this matters:** Running `mypy packages/` on source files alone doesn't trigger import resolution the way CI does. The `-e` flag installs nanobot as a package, so mypy resolves `from yaml import` to the installed package and checks stub availability. This is how the CI mypy failure was reproduced locally.

**Key trigger files:** `packages/nanobot/nanobot/skills.py` and `packages/nanobot/nanobot/channels/cron/service.py` both use `from yaml import` and `from croniter import` — must be excluded in pyproject.toml mypy config.

## CI Not Triggering (Separate Problem)

`.github/workflows/ci.yml` IS in the path filter (`*.yml`), so changes SHOULD trigger CI. If CI doesn't run after pushing a workflow change:

1. The push may not have reached GitHub yet (wait 30s and re-check)
2. Force with a trivial tracked-file change (e.g., pyproject.toml description tweak)
3. Or dispatch via GitHub API:
```bash
curl -s -X POST \
  -H "Authorization: token $GH_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/ChonSong/agent-os/actions/workflows/269405069/dispatches" \
  -d '{"ref":"main"}'
```

## GitHub API CI Status Check (No gh CLI)

```python
import urllib.request, json
token = 'ghp_...'  # from memory
headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github+json'}

# Get latest run
req = urllib.request.Request(
    'https://api.github.com/repos/ChonSong/agent-os/actions/runs?per_page=3',
    headers=headers
)
with urllib.request.urlopen(req, timeout=10) as r:
    d = json.loads(r.read())
    for x in d['workflow_runs'][:3]:
        print(x['id'], x['head_sha'][:8], x['conclusion'] or x['status'])

# Get jobs for specific run
req2 = urllib.request.Request(
    f'https://api.github.com/repos/ChonSong/agent-os/actions/runs/{RUN_ID}/jobs',
    headers=headers
)
with urllib.request.urlopen(req2, timeout=10) as r:
    d = json.loads(r.read())
    for j in d['jobs']:
        print(f"Job: {j['name']} | {j.get('conclusion','-')}")
        for s in j.get('steps', []):
            if s.get('conclusion') == 'failure':
                print(f"  FAILED STEP: {s['name']}")
```

## Observability Test Rounding Bug (Pre-existing)

`test_drift_score_partial_correction` in `packages/observability/tests/test_events.py` expected 66 but function returns 67 (Python rounds 2/3*100 = 66.66 → 67). This was a pre-existing bug masked by earlier CI failures.

## Docker Compose Long-Running Process Detection

`docker compose up -d` (even with `-d`) is flagged as a long-lived server process by the hermes terminal tool, causing it to fail with "Foreground command appears to start a long-lived server/watch process."

**Workaround:** Use SSH with explicit batch mode:
```bash
ssh -i /opt/data/home/.hermes/home/.ssh/id_ed25519 \
    -o BatchMode=yes \
    sean@localhost \
  'docker compose up -d; docker compose ps'
```

## GHCR Image Tag Syntax in GitHub Actions (CRITICAL)

**`toLower()` is NOT valid GitHub Actions expression syntax.** The `| lower` Jinja2-style filter also doesn't work. Both result in a bad tag like `ghcr.io/ChonSong/...` (uppercase owner) which GHCR rejects with `invalid tag ... repository name must be lowercase`.

**Fix:** Hardcode the lowercase org path:
```yaml
# WRONG — produces ChonSong (uppercase):
ghcr.io/${{ github.repository_owner }}/agent-os:${{ github.sha }}
ghcr.io/${{ toLower(github.repository_owner) }}/agent-os:${{ github.sha }}
ghcr.io/${{ github.repository_owner | lower }}/agent-os:${{ github.sha }}

# RIGHT — hardcode lowercase:
ghcr.io/chonsong/agent-os:${{ github.sha }}
ghcr.io/chonsong/agent-os:latest
```

## Deploy Step Silent Failure — Missing Secrets

The `webfactory/ssh-agent` action can fail silently if `secrets.DEPLOY_SSH_KEY` is not set, causing the deploy job to exit non-zero. The fix is a pre-check step:

```yaml
- name: Validate deploy secrets
  id: validate-secrets
  run: |
    if [ -z "${{ secrets.DEPLOY_SSH_KEY }}" ]; then
      echo "skip_deploy=true" >> "$GITHUB_OUTPUT"
      echo "ERROR: DEPLOY_SSH_KEY secret is not set. Skipping deploy."
    else
      echo "skip_deploy=false" >> "$GITHUB_OUTPUT"
    fi

- name: Setup SSH
  uses: webfactory/ssh-agent@v0.8.0
  if: steps.validate-secrets.outputs.skip_deploy == 'false'
  with:
    ssh-private-key: ${{ secrets.DEPLOY_SSH_KEY }}
```

When the SSH key is missing, the job logs will show:
```
ERROR: DEPLOY_SSH_KEY secret is not set. Skipping deploy.
```

**Required GitHub secrets for auto-deploy:** `DEPLOY_SSH_KEY` (private key matching server's `authorized_keys`), `DEPLOY_HOST` (server IP/hostname), `DEPLOY_USER` (e.g. `sean`).

## Deploy Step Silent Failure — Wrong Secret Name

**`DEPLOY_SSH_KEY` is NOT the correct secret name.** The actual secret is `DEPLOY_KEY`. The validation step checks `secrets.DEPLOY_SSH_KEY` which is always empty → deploy silently skipped.

**Server is also behind ISP NAT (port 22 blocked).** SSH-based deploy from CI never works regardless. Switch to webhook-based deploy (`POST /api/deploy`).

```yaml
# WRONG (always skips):
if [ -z "${{ secrets.DEPLOY_SSH_KEY }}" ]; then

# RIGHT:
if [ -z "${{ secrets.DEPLOY_KEY }}" ]; then
```

## CI Not Triggering — paths-ignore

If a push doesn't trigger CI, check if only `paths-ignore` files changed:

```yaml
# In agent-os.yml push trigger:
push:
  branches: [main]
  paths-ignore:
    - 'README.md'
    - '*.md'
    - 'docs/**'
```

Push a file outside these patterns (e.g. `docker-compose.yml`, `apps/**`, `infra/**`) to trigger CI. Use `workflow_dispatch` for manual runs (but note: it skips `needs:` dependent jobs — use `push` to main for full pipeline).

## CI Job Logs Expire (404 from GitHub API)

GitHub expires workflow run logs after ~90 days (or immediately for certain configurations). When logs are expired:
- `GET /actions/runs/{id}/jobs` returns `{"total_count": 0, "jobs": []}`
- `GET /actions/runs/{id}/logs` returns 404

**The run metadata (conclusion, status) is still accessible** via `GET /actions/runs/{id}` even after logs expire. The failure is real — only the per-job/step breakdown is hidden.

**Workaround:** Add a diagnostic pre-check step that `echo`s secret configuration status to stdout — it appears in the run's own logs before potential failure.

## GHCR Full SHA Tag Required for docker pull

Short tags (7-char SHA like `82d1844`) don't resolve in GHCR. Use the **full 40-char SHA** when pulling:
```bash
# WRONG:
docker pull ghcr.io/chonsong/agent-os:82d1844
# Error: not found

# RIGHT:
docker pull ghcr.io/chonsong/agent-os:82d1844f6536fb6ff2ff2b3adbb0f321e0abb562
```

To find the full SHA for a tag, query the GHCR API:
```python
import urllib.request, json
token = 'ghp_...'  # GitHub token with read:packages scope
req = urllib.request.Request(
    'https://api.github.com/users/ChonSong/packages/container/agent-os/versions',
    headers={'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}
)
with urllib.request.urlopen(req) as r:
    for v in json.loads(r.read()):
        tags = v.get('metadata', {}).get('container', {}).get('tags', [])
        print(tags, v['created_at'][:10])
```

## PostgreSQL UUID vs TEXT Cross-Table Comparisons

`agent_sessions.id` is UUID type; `dashboard_sessions.id` is TEXT. Comparisons between them fail with `operator does not exist: text = uuid` even when the string values look identical (both are string representations of UUIDs).

**Correct cast — cast UUID to text:**
```sql
-- WRONG:
SELECT 1 FROM dashboard_sessions WHERE id = agent_sessions.id
-- Error: operator does not exist: text = uuid

-- RIGHT (cast UUID column to text):
SELECT 1 FROM dashboard_sessions WHERE id::text = agent_sessions.id
```

**To check column types:**
```sql
SELECT column_name, data_type, udt_name
FROM information_schema.columns
WHERE table_name IN ('agent_sessions', 'dashboard_sessions')
AND column_name = 'id';
```

Or via Docker:
```bash
docker exec agent-os-postgres psql -U agentos -d agentos \
  -c "SELECT column_name, data_type, udt_name FROM information_schema.columns WHERE table_name IN ('agent_sessions', 'dashboard_sessions') AND column_name = 'id';"
```

Or inspect oid from within the backend container:
```bash
docker exec agent-os-backend node -e "
const { Pool } = require('pg');
const pool = new Pool({ connectionString: process.env.DATABASE_URL });
pool.query('SELECT id FROM dashboard_sessions LIMIT 1').then(r => {
  console.log('dashboard_sessions cols:', r.fields.map(f => f.name + ':' + f.dataTypeID));
  return pool.query('SELECT id FROM agent_sessions LIMIT 1');
}).then(r => {
  console.log('agent_sessions cols:', r.fields.map(f => f.name + ':' + f.dataTypeID));
  pool.end();
}).catch(e => { console.error(e.message); pool.end(); });
"
```
OID 2950 = UUID type in PostgreSQL. OID 25 = TEXT type.

## CI Multi-Commit Layered Failure Pattern (Confirmed Again)

Same pattern as before — 6+ consecutive commits to fix a cascade of CI issues:
1. `24dba66` — added workflow_dispatch trigger (toLower still bad)
2. `87560ab` — hardcoded `chonsong` lowercase (still had echo debug code)
3. `d37d77e` — clean debug echo addition
4. `82d1844` — added `--force-recreate` to deploy
5. `b11a80d` — removed erroneous ::text cast (cast was wrong direction — compared UUID to TEXT with no cast)
6. `906e9a3` — cast `agent_sessions.id::text` (UUID→text, correct)
7. `1746174` — added `last_active` and `preview` to sessions API

Each fix revealed the next issue. Always wait for full CI completion before declaring success.

## Docker Build Cache — Silent Stale Builds

**`--no-cache` does NOT always produce a fresh build.** Docker's build cache has multiple layers:
- Image layer cache (reused via `FROM` statements)
- Build cache mounts (`RUN --mount=type=cachemount`) — these persist across `--no-cache` builds
- BuildKit inline cache (`--build-arg BUILDKIT_INLINE_CACHE=1`)

If a build passes but the deployed container still has old behavior despite `--no-cache`, the `exec.cachemount` type is likely reusing compiled artifacts. Fix:
```bash
docker builder prune --filter type=exec.cachemount
# or for completely fresh:
docker builder prune -a
```

**ts-build stage caching:** The TypeScript compilation (`npx turbo build`) runs in a dedicated stage. If layer caching preserves the compiled `dist/` from a prior build, your new code never gets deployed even though the build "succeeds." Always check:
```bash
# Verify the deployed container has your new code:
docker exec agent-os-backend grep 'YOUR_NEW_STRING_OR_ROUTE' /app/apps/dashboard/backend/dist/index.js
```

## ContainerInfo TypeScript Incompleteness

`ContainerInfo` from `@types/dockerode` does not expose `Image`, `Names`, `Env`, `Cmd`, `Entrypoint`, `WorkingDir`, `HostConfig`, or `NetworkSettings.Networks` at the type level — they exist at runtime but the TypeScript type is incomplete.

**Pattern — always cast to `any`:**
```typescript
const containers = await docker.listContainers({ all: true });
const info = containers[0] as any;
console.log(info.Image);      // works — TS error without `as any`
console.log(info.HostConfig); // works — TS error without `as any`
console.log(info.Names);      // works — TS error without `as any`
console.log(info.Env);        // works — TS error without `as any`
```

Never destructure these from `ContainerInfo` directly — `const { Image, Names } = c` will fail TS compilation.

## execSync Inside Containers Runs on Host

When using `execSync` (from `child_process`) inside a container, it runs on the **host filesystem** via the Docker socket, NOT inside the container. This means:
- `execSync('pwd')` returns `/home/sean/.hermes/agent-os` (host home dir), not `/app`
- `execSync('docker pull ...')` calls the **host's** `docker` binary (which may be aliased to `buildx build`)
- Paths in execSync commands are host paths, not container paths

**Do not use execSync for container management inside a container** — use dockerode instead (it communicates via the socket, properly scoped to the Docker API).

## GHA Runner Network Isolation — All Push Approaches Fail (CRITICAL)

**Discovery (2026-05-06):** GitHub Actions runners have network isolation that prevents the runner shell from reaching `ghcr.io` for push operations. This is NOT a credentials, authentication, or configuration issue — it is a fundamental GHA network architecture limitation.

**Symptoms:**
- Every approach to pushing to GHCR from GHA fails at the push step
- Approaches tried and failed: `docker/setup-buildx-action` + `docker/login-action` + `docker/build-push-action@v6` (load:false,push:true), plain `docker buildx build --push`, plain `docker tag && docker push` (even after `docker login`), crane push, Kaniko
- The build step succeeds every time — only the push fails
- `docker push` from the server works perfectly (server has different network access)
- The GHCR registry IS reachable from the runner for some operations (login succeeds, sometimes initial push appears to succeed) but subsequent operations or actual image push always fails

**The build itself always works:** `docker build-push-action` with `load: true` (daemon mode) builds and loads into the local docker daemon successfully. The failure is at the registry push step.

**Working approach: Artifact-based pipeline**
1. **Build job:** Build with `load: true`, save image via `docker save` to a `.tar` file, upload as a GitHub Actions artifact
2. **Server-side download:** Backend implements `GET /repos/{repo}/actions/artifacts` (GitHub API) to find artifact ID, then `GET /repos/{repo}/actions/artifacts/{id}/archive` to download the `.tar`
3. **Load and push from server:** `docker load < archive.tar`, `docker push` from the server (which CAN reach GHCR)

**Why artifact download works:** GHA artifacts are served from `https://pipelines.actions.githubusercontent.com` — a different domain than GHCR. The server can reach this domain; it cannot reach `ghcr.io` from the GHA runner shell.

**Draft workflow (build job):**
```yaml
- name: Build image
  uses: docker/build-push-action@v6
  with:
    context: .
    load: true
    push: false
    tags: ghcr.io/${{ github.repository }}:${{ github.sha }}

- name: Save image as artifact
  run: |
    docker save ghcr.io/${{ github.repository }}:${{ github.sha }} -o /tmp/agent-os.tar

- name: Upload image artifact
  uses: actions/upload-artifact@v4
  with:
    name: agent-os-image-${{ github.sha }}
    path: /tmp/agent-os.tar
    retention-days: 2
```

**Draft backend endpoint for server-side pull:**
```
POST /api/deploy/pull-from-gha
Body: { run_id, sha, repo, token }
→ Server fetches artifact from GitHub API
→ docker load < downloaded.tar
→ docker tag + docker push (from server, where GHCR is reachable)
→ docker compose up -d backend --pull always
```

## Proxy-Based i18n + Record<string, unknown> = TS18046 Cascade (CRITICAL)

When using a Proxy-based i18n system where `t.common.xxx`, `t.skills.xxx` etc. are resolved dynamically through nested proxies, the return type of property access MUST be `any`, NOT `unknown`. Using `Record<string, unknown>` causes `TS18046: 't.common' is of type 'unknown'` on every single `t.*` access across the entire codebase — potentially hundreds of errors.

**Wrong:**
```typescript
export type I18n = Record<string, unknown>;
```

**Right:**
```typescript
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type I18n = Record<string, any>;
```

**Why:** Proxy `get` traps return the dynamically-resolved value. TypeScript cannot infer the concrete type through the proxy chain, so it falls back to the declared type. If that's `unknown`, every property access on the result is a type error. This is fundamentally different from a simple object where TS can resolve the shape.

**Pattern:** This class of bug manifests as a build failure with a huge number of TS18046 errors all pointing to `t.*` accesses. The fix is always the same — change the type to `any`. Do NOT attempt to type the proxy return more specifically.

## Card→div Bento Migration Produces Mismatched JSX Nesting

When converting `<Card>/<CardHeader>/<CardTitle>/<CardContent>` to raw `<div>/<span>`, the component API mismatch causes nesting errors:

- `Card` → `div` (1:1)
- `CardHeader` → `div` (but CardHeader was sometimes implicitly closed by CardTitle/CardContent)
- `CardTitle` → `span` (different element type, but old closing `</CardTitle>` → `</span>`)
- `CardContent` → `div` (but may introduce an extra nesting level)

**Common errors:**
- Extra `</div>` where `</CardContent></Card>` was two closes but the replacement only needs one
- Missing opening `<span>` where `<CardTitle>` was replaced with just the closing `</span>`
- `</div>` at depth -1 (more closes than opens)

**Detection (div balance check):**
```python
import re
lines = open("file.tsx").readlines()
depth = 0
for i, line in enumerate(lines, 1):
    opens = len(re.findall(r'<div[\s>]', line))
    closes = len(re.findall(r'</div>', line))
    depth += opens - closes
    if depth < 0:
        print(f"UNDERCLOSE at line {i}: depth={depth}")
# Note: self-closing <div.../> counts as open in regex but doesn't need </div>
# Subtract: self_closing = len(re.findall(r'<div[^>]*/>', content))
```

**Fix pattern:** Compare original and converted side by side. The original `</CardHeader>` + `</Card>` is two closes. The replacement `</span>` + `</div>` + `</div>` might be three. Count carefully.

## H2 Component Variant Constraint

`NouiTypography`'s `H2` component only accepts `variant?: "sm" | "md" | "lg" | "xl"`. Using `variant="xs"` causes `TS2322`. Use `variant="sm"` for small text.

## Express.text() vs express.raw() for Webhook Bodies

When a webhook handler receives a plain-text body (not JSON), `express.raw()` fails to parse it with `SyntaxError: Unexpected token`. Use `express.text()` instead:
```typescript
// WRONG — for JSON only:
app.post('/api/deploy', express.raw({ type: 'application/json' }), async (req, res) => {
  // req.body is a Buffer, JSON.parse fails on plain text
});

// RIGHT — accept plain text:
app.post('/api/deploy', express.text(), async (req, res) => {
  const token = (req.body as string).trim();
});
```
