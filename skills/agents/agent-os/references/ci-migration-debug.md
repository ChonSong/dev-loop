# CI, Migration & Deployment Debug Reference

## CI Debugging via GitHub API (Python)

The `gh` CLI is not always available. Use Python urllib directly:

```python
import urllib.request, json

def get_runs(n=3):
    req = urllib.request.Request(
        'https://api.github.com/repos/ChonSong/agent-os/actions/runs?per_page=%d' % n,
        headers={'Accept': 'application/vnd.github+json',
                 'Authorization': 'Bearer ghp_YOUR_TOKEN'}
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

def get_failing_jobs(run_id):
    req = urllib.request.Request(
        f'https://api.github.com/repos/ChonSong/agent-os/actions/runs/{run_id}/jobs',
        headers={'Accept': 'application/vnd.github+json',
                 'Authorization': 'Bearer ghp_YOUR_TOKEN'}
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

# Latest 3 runs:
for r in get_runs(3)['workflow_runs']:
    print(r['head_sha'][:7], r['conclusion'] or r['status'])

# Failing job IDs:
jobs = get_failing_jobs(RUN_ID)
for j in jobs['jobs']:
    if j.get('conclusion') == 'failure':
        print(j['id'], j['name'])
```

**GH jobs API returns empty:** `{"total_count": 0, "jobs": []}` for recently-completed runs. Workaround: use `conclusion` from the run list (always populated). Only per-job detail is unreliable for recent runs.

## MCP Server CI Failure Chain (cloudflare-zero-trust/server.py)

Three consecutive CI failures from one file:

| Push | Error | Fix |
|------|-------|-----|
| 1 | `F821` `json` undefined (33 errors), `os` undefined (33 errors) | No imports at all — add `import json`, `import os` |
| 2 | `F821` `httpx` undefined (5 errors) | Add `import httpx` |
| 3 | `E401` multiple imports on one line | Split: `import json`, `import os`, `import httpx` (one per line) |

**Rule:** CI ruff runs with E401 (one-per-line imports). Each import goes on its own line. Always verify: `ruff check packages/mcp-servers/cloudflare-zero-trust/server.py`.

## Migration Runner: Hardcoded Array (Not Dynamic Scan)

The backend migration runner in `apps/dashboard/backend/src/index.ts` uses a **hardcoded array** — it does NOT scan the filesystem. Files added to `infra/postgres/migrations/` but NOT in the `migrationFiles` array are silently skipped.

```typescript
// apps/dashboard/backend/src/index.ts
const migrationFiles = [
  '001_initial.sql',
  '002_observability_tables.sql',
  // ... MUST manually add each new migration here
];
```

Adding a migration requires BOTH:
1. `infra/postgres/migrations/XXX_*.sql` file created
2. Filename added to `migrationFiles` array in `index.ts`

## PostgreSQL NOW() Not IMMUTABLE

`NOW()` returns the current transaction timestamp, which is stable within a transaction but NOT immutable across executions. PostgreSQL requires index predicate functions to be marked `IMMUTABLE`.

```sql
-- WRONG — fails with "functions in index predicate must be marked IMMUTABLE":
CREATE INDEX idx_aie_events_recent ON aie_events(timestamp)
  WHERE NOW() - timestamp < interval '1 day';

-- RIGHT — use a constant or a pure timestamp comparison:
CREATE INDEX idx_aie_events_recent ON aie_events(timestamp DESC)
  WHERE timestamp > NOW() - interval '1 day';
```

Or: don't use partial indexes with time functions — just use a regular composite index and filter in the query.

## Memory Limits (docker-compose.yml)

Increased 2026-05-07 to prevent OOM kills from webhook event storm:

| Service | Old | New |
|---------|-----|-----|
| nanobot | 512m | 1g |
| backend | 512m | 1g |
| cloudflared | 256m | 1g |
| webhook-emitter | 256m | 256m |

**OOM root cause:** The webhook-emitter generates 4-8 Docker container state change events every 10 seconds. The backend subscribes to Docker events and inserts into `aie_events` table. At 5,600+ events in the DB, the backend's `/api/status` endpoint runs 10+ N+1 subqueries against the events table, causing memory pressure. With 512m limit, the backend was OOM-killed (exit 137) on every deploy cycle.

**Diagnosis:** `docker stats agent-os-backend --no-stream` showed 45MB / 512MB. `docker logs agent-os-backend | grep "Migration error"` showed migration failures but didn't explain the OOM. `docker inspect agent-os-backend | grep -i oom` confirmed OOM kill.

## Git add -A Re-appearing Files

Files that keep appearing as untracked after `git add -A`:
- `packages/mcp-servers/cloudflare-zero-trust/server.py` (from gitignored location)
- `scripts/hermes-state-migrate.sh`

**Always stage explicit paths:**
```bash
git reset HEAD
git add apps/dashboard/backend/src/index.ts
git commit -m "descriptive message"
```

## Docker Action Safety: Backend Can't Stop Itself

The `POST /api/docker/containers/:id/:action` endpoint (stop/restart/remove) uses Dockerode on the backend container itself. If the backend container ID matches the requested action target, the request kills the backend.

**Fix applied (2026-05-07):** The endpoint now inspects the target container ID and compares it to `process.env.HOSTNAME` (backend's container hostname). If they match, returns `400 Cannot control the backend container from itself`.

## Docker API Path Params vs Query Params

Some backend routes use path parameters, others use query parameters. Test both:

```python
# Path param (route: /api/files/{path:.*})
curl http://localhost:3001/api/files/home/sean

# Query param (route: /api/files?path=...)
curl "http://localhost:3001/api/files?path=/home/sean"
```

The FileExplorerPage frontend uses path params. `curl` from host uses path params. `fetch()` in the browser uses whatever the frontend calls. Verify which the route handler expects before debugging "empty results".
