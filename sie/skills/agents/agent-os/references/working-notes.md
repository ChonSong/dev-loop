# agent-os Working Notes (2026-05-07 session)

## 6 Un-routed Pages Discovered and Wired

Six fully-built pages (3,600+ lines of UI) existed in `apps/dashboard/frontend/src/pages/` but had no App.tsx route or Sidebar nav entry:

- `ConfigPage` (614 lines) — `/config` — YAML config editor, schema-aware form
- `EnvPage` (872 lines) — `/env` — Environment variables CRUD with reveal/delete
- `LogsPage` (233 lines) — `/logs` — Real-time log viewer with level/component/file filters
- `ModelsPage` (817 lines) — `/models` — Model picker, assignment, per-model analytics
- `ChatPage` (834 lines) — `/chat` — Full hermes TUI terminal in browser (xterm.js + WebSocket PTY)
- `DocsPage` (61 lines) — `/docs` — Documentation viewer

All six have working backend endpoints. Routing them required:
1. Adding imports to `App.tsx`
2. Adding `<Route path="/..." element={<Page />} />` entries
3. Adding `{ path, label, icon }` to `Sidebar.tsx`'s `NAV_ITEMS` array
4. Importing any new icons from `lucide-react`

**State after 2026-05-07 session:**
- 16 pages routed in App.tsx (was 10 before this session)
- 32/32 backend API endpoints verified returning 200 (0 failed)
- 8 consecutive CI greens
- 5/5 containers healthy
- 8/8 migrations applied (001_initial through 008_fix_indexes)
- 7 performance indexes on aie_events, agent_messages, dashboard_sessions
- Accessible at `https://agent-os.codeovertcp.com`

## Docker Layer Cache Pitfall

**IMPORTANT: Docker layer cache can silently reuse stale code.** If a build passes but the deployed container still has old behavior, the ts-build layer may be cached from a prior state. Always use `--no-cache` when you need a clean build (code changes, changed entrypoint, new packages). If stale behavior persists despite `--no-cache`, clear the build cache explicitly:

```bash
docker builder prune --filter type=exec.cachemount
# or for a completely fresh start:
docker builder prune -a
```

**Also: disk at 100% causes silent cache staleness.** When the host disk fills up, buildkit cannot allocate snapshot space and silently falls back to cached layers — build reports success but doesn't rebuild. See `references/docker-disk-full-build-cache.md` for diagnosis and fix.

## Disk Full Emergency (Host Disk 100%)

```bash
# Safe commands that won't kill running containers:
docker image prune -f     # removes dangling images only — safe, fast
docker builder prune -f   # removes build cache — reclaim 1-5 GB

# DO NOT run these on a full disk — they hang indefinitely:
docker system prune -f --volumes   # HANGs on 100% disk
docker system prune -a            # HANGs on 100% disk

# After reclaiming space, restart crashed containers:
docker restart agent-os-postgres
```

## `git add -A` Pitfall

Files like `packages/mcp-servers/cloudflare-zero-trust/server.py` and `scripts/hermes-state-migrate.sh` keep appearing as untracked. Always stage explicit paths only:
```bash
git reset HEAD                                    # clean slate
git add apps/dashboard/frontend/src/App.tsx      # explicit
git commit -m "message"
```
If accidentally committed unrelated files:
```bash
git reset --soft HEAD~1          # undo commit, keep staged
git rm --cached <unwanted-file>  # unstage unwanted
git commit -m "correct message"
```

## AppStorePage ESLint vs TypeScript

Template array bugs (duplicate keys, missing fields) compile fine in TypeScript but fail ESLint in CI. ESLint runs AFTER TypeScript in CI and uses `--report-unused='directive'` which errors on `console.error`. Always run both before pushing:
```bash
npx --yes tsc --noEmit       # TypeScript — CLEAN
npx --yes eslint src/pages/AppStorePage.tsx  # ESLint — catches duplicates/missing fields
```

## Python Lint + MCP Server Imports — CRITICAL for CI

The MCP server at `packages/mcp-servers/cloudflare-zero-trust/server.py` MUST have proper imports. Three consecutive CI failures were caused by this file:
1. Missing `import json` and `import os` (F821 undefined names — 33 errors)
2. Missing `import httpx` (F821 undefined name httpx — 5 errors)
3. `import json, os` (E401 multiple imports on one line — 1 error)

**Correct import block (must match CI's ruff rules exactly):**
```python
#!/usr/bin/env python3
# Cloudflare Zero Trust MCP Server
import json
import os
import httpx
```
- Each import on its own line (E401 violation otherwise)
- Both `json` and `os` are required at module level even if used only in function bodies
- `httpx` is required for the HTTP client calls throughout the file
- Always verify with ruff locally before pushing: `ruff check packages/mcp-servers/cloudflare-zero-trust/server.py`