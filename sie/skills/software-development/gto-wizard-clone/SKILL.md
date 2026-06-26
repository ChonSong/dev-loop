---
name: gto-wizard-clone
description: GTO Wizard Clone — open-source poker training platform with full worker/Celery async task queue
tags: [poker, game-theory-optimal, monte-carlo, mccfr, cfr, fastapi, nextjs, tailwind, equity, celery, worker, design]
related_skills: [systematic-debugging, test-driven-development, docker-patterns, container-process-forensics, e2e-testing, cron-job-patterns]
---

# GTO Wizard Clone

Repo: `ChonSong/gto-wizard-clone` at `/workspace/gto-wizard-clone`
gto_poker pip-installed as editable from `/workspace/gto-wizard-clone/packages/poker-core`

## Architecture Overview

**Monorepo**: 4 apps + 3 packages, turbo workspaces
- `apps/web` — Frontend (Next.js 15 + React 19 + Tailwind v4 + Shadcn UI)
- `apps/api` — Backend (FastAPI + WebSocket)
- `apps/solver` — GTO Solver (Python MCCFR)
- `apps/worker` — Celery task queue (15 tasks, 3 queues)
- `packages/poker-core` — Shared poker logic (7 variants, 368 tests)
- `packages/types` — Shared TypeScript types
- `packages/ui-components` — Shared UI components

**7 Game Variants**: NLH, PLO4, PLO5, Omaha Hi/Lo, Shortdeck, Double Board PLO, Bomb Pot

**Worker queues**: `solver` (10 tasks), `analysis` (3 tasks), `default` (2 tasks)

## Worker / Celery Architecture (stale — now replaced by direct gRPC)

> **⚠️ June 2026: The Celery solve path has been replaced by a direct gRPC solver backend.** The FastAPI solver router now connects to the gRPC solver server via `apps/api/services/solver_client.py`. Celery code still exists in `apps/worker/` but is no longer the primary solve path. This section is kept for reference.

The worker layer handles all async/background work: CFR solving, variant equity, batch HH analysis, leak detection, push/fold chart generation, and job cleanup.

### File Layout

```
apps/worker/
├── celery_app.py          # App creation, task routing, beat schedule
├── tasks.py               # 15 registered tasks
├── Dockerfile             # Installs poker-core + solver packages first
└── requirements.txt       # celery[redis], redis, numpy, pydantic, sqlalchemy, asyncpg
```

### Celery App Pattern (`celery_app.py`)

```python
import os, sys
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, 'packages', 'poker-core', 'src'))
sys.path.insert(0, os.path.join(REPO_ROOT, 'apps', 'solver'))
sys.path.insert(0, os.path.join(REPO_ROOT, 'apps', 'api'))

celery_app = Celery("gto_solver", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND,
                    include=["apps.worker.tasks"])
app = celery_app  # alias
```

**Key config:**
- `task_time_limit=7200` (2hr hard), `task_soft_time_limit=6600` (1h50min soft)
- `worker_prefetch_multiplier=1`, `worker_max_tasks_per_child=20`
- `task_acks_late=True`, `task_reject_on_worker_lost=True`
- `result_expires=86400`

**Task routes** map task names → queues:
- `solver` queue: `solver.solve_spot`, `solver.solve_flop_spot`, `solver.solve_turn_spot`, `solver.solve_plo4_spot`, `solver.solve_omaha_spot`, `solver.solve_shortdeck_spot`, `solver.solve_double_board_equity`, `solver.solve_bomb_pot_equity`, `solver.compute_push_fold_chart`, `solver.submit_solve`
- `analysis` queue: `analysis.batch_import_hands`, `analysis.analyze_leaks`, `analysis.compute_icm_batch`
- `default` queue: `solver.get_job_status`, `maintenance.cleanup_expired_jobs`

**Beat schedule**: `maintenance.cleanup_expired_jobs` daily at 3 AM UTC

### Task Registration Pattern (`tasks.py`)

**CRITICAL — avoid circular imports:**
```python
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from apps.worker.celery_app import get_progress_channel  # module-level is OK

# DON'T import celery_app here — use lazy import inside functions:
def submit_solve(params):
    from apps.worker.celery_app import celery_app  # lazy import
    celery_app.send_task("solver.solve_spot", args=[params])
```

Use `@shared_task(name="...", queue="...")` decorators. All long-running tasks: `max_retries=2`, `SoftTimeLimitExceeded` triggers retry with halved iterations/samples.

### Progress Publishing Pattern

```python
def publish_progress(job_id, progress, status, extra=None):
    channel = f"solver:progress:{job_id}"
    msg = {"job_id": job_id, "progress": progress, "status": status, "timestamp": time.time()}
    if extra: msg.update(extra)
    client = redis.Redis.from_url(CELERY_BROKER_URL)
    client.publish(channel, json.dumps(msg))
    client.set(f"job:status:{job_id}", json.dumps(msg), ex=86400)
```

### Redis → WebSocket Bridge (`apps/api/services/progress_bridge.py`)

`ProgressBridge` singleton subscribes to Redis pattern `solver:progress:*` and forwards to `WebSocketManager.broadcast_to_job()` via `asyncio.run_coroutine_threadsafe()`.

```python
class ProgressBridge:
    _instance = None
    _lock = threading.Lock()  # class-level, not instance-level

    def __init__(self):
        self._redis_service = get_redis_service()
        self._ws_manager = get_websocket_manager()
        self._loop = None
        self._running = False

    @classmethod
    def register(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            if not cls._instance._running:
                cls._instance.start()
            return cls._instance

    def _on_progress(self, data):
        job_id = data.get("job_id")
        if not job_id or not self._loop:
            return
        asyncio.run_coroutine_threadsafe(
            self._ws_manager.handle_solver_progress(job_id, data), self._loop)
```

`RedisService._listen_for_updates()` uses `psubscribe` for pattern channels, handles both `message` and `pmessage` types.

**Wiring in `main.py`:**
- Startup: `ProgressBridge.register()` after `init_redis()`
- Shutdown: `ProgressBridge._instance.stop()`

### Worker Dockerfile Pattern

**CRITICAL — install monorepo packages BEFORE worker source:**
```dockerfile
FROM python:3.12-slim
COPY apps/worker/requirements.txt .
RUN pip install -r requirements.txt
COPY packages/poker-core ./packages/poker-core
RUN pip install -e ./packages/poker-core    # MUST be before worker
COPY apps/solver ./apps/solver
RUN pip install -e ./apps/solver            # MUST be before worker
COPY apps/api ./apps/api
COPY apps/worker/ ./apps/worker/
CMD ["celery", "-A", "apps.worker.celery_app", "worker",
     "--loglevel=info", "--concurrency=4", "-Q", "solver,analysis,default"]
```

### docker-compose Worker Services

```yaml
worker:
  build: { context: ., dockerfile: apps/worker/Dockerfile }
  command: celery -A apps.worker.celery_app worker --loglevel=info --concurrency=4 -Q solver,analysis,default
  environment:
    CELERY_BROKER_URL: redis://redis:6379/1
    CELERY_RESULT_BACKEND: redis://redis:6379/2

beat:
  build: { context: ., dockerfile: apps/worker/Dockerfile }
  command: celery -A apps.worker.celery_app beat --loglevel=info
```

### New API Endpoints for Worker Tasks

| Endpoint | Method | Task | Queue |
|----------|--------|------|-------|
| `/api/v1/solver/solve` | POST | Routes by variant/street | solver |
| `/api/v1/solver/solve/double-board` | POST | `solver.solve_double_board_equity` | solver |
| `/api/v1/solver/solve/bomb-pot` | POST | `solver.solve_bomb_pot_equity` | solver |
| `/api/v1/solver/solve/plo4` | POST | `solver.solve_plo4_spot` | solver |
| `/api/v1/solver/analysis/import-hands` | POST | `analysis.batch_import_hands` | analysis |
| `/api/v1/solver/analysis/leaks` | POST | `analysis.analyze_leaks` | analysis |
| `/api/v1/solver/analysis/push-fold-chart` | POST | `solver.compute_push_fold_chart` | solver |
| `/api/v1/solver/status/{job_id}` | GET | `solver.get_job_status` | default |
| `/api/v1/solver/ws/{job_id}` | WebSocket | Real-time progress | — |

## Key Worker Pitfalls

### Circular Import (CRITICAL)
`celery_app.py` imports `tasks.py` via `include=[]`. `tasks.py` must NOT import `celery_app` at module level. Use `shared_task` decorators and lazy `from apps.worker.celery_app import celery_app` inside functions.

### Worker Package Access
Worker imports from `packages/poker-core` and `apps/solver`. Dockerfile MUST install these as editable packages before copying worker source. Worker CMD must specify `-Q solver,analysis,default`.

### Redis Pattern Subscribe
Use `RedisService.subscribe_to_progress(job_id="*")` for wildcard. Internally uses `psubscribe` in `_listen_for_updates()`. The `_InMemoryStub` doesn't support pattern subscribe — falls back to exact match (works with fakeredis).

### Event Loop in Celery Tasks
Never create `asyncio.new_event_loop()` in Celery worker's main thread (deadlocks with prefork). Use `ThreadPoolExecutor` with a dedicated loop per call for async DB operations.

### Strategy Storage in Tasks
Strategy storage after solving: use `ThreadPoolExecutor(max_workers=1)` with a dedicated event loop. Wrap in try/except — never let storage failures fail the solve task.

## Access (June 2026 — updated for direct gRPC)

**Repo source path (HOST — this is the real deployment):** `/home/sean/gto-wizard-clone`
**Container path:** `/workspace/gto-wizard-clone` (keep in sync via git push/pull)

- **gRPC Solver**: Port 50051 on HOST — run `python3 -m apps.solver.server` from repo root
- **Frontend**: `/home/sean/gto-wizard-clone/apps/web` on port **8564** (Next.js 15, host-managed auto-restart)
- **API**: Port **8003** on HOST — run from `apps/api/` with `PYTHONPATH='..'` (to resolve `from routers import X`)
- **DB**: SQLite at `/home/sean/gto-wizard-clone/gto_wizard.db`
- **Public**: https://wiz.codeovertcp.com via Cloudflare tunnel (tunnel ID: 24362d8c)
- **Source**: `ChonSong/gto-wizard-clone`

### API start command (current)

```bash
cd /home/sean/gto-wizard-clone/apps/api
PYTHONPATH='..' nohup /home/sean/hermes-apps-venv/bin/uvicorn main:app --host 0.0.0.0 --port 8003 --log-level warning > /tmp/gto-api.log 2>&1 &
```

### Solver gRPC server start command

```bash
cd /home/sean/gto-wizard-clone
nohup /home/sean/hermes-apps-venv/bin/python3 -m apps.solver.server > /tmp/solver-grpc.log 2>&1 &
```

### Solve path

**FastAPI POST /api/v1/solver/solve** → `apps/api/services/solver_client.py` (gRPC client) → `localhost:50051` → `SolverServicer.SubmitSolve()` → MCCFR engine → strategy response

This replaces the old: API → Celery task queue → worker process → solver engine.

### Direct gRPC Solve (bypass Celery)

The gRPC client connects to the solver server directly. Solves are synchronous (blocking until complete) but fast for river/flop spots with low iteration counts. For the study page, direct gRPC is the correct path:

```python
from services.solver_client import submit_solve

result = submit_solve(
    game_type="nlh",
    players=2,
    board="Kd7h2c",
    pot_size=100,
    stack_depth=100,
    iterations=500,
    street="river",
    position="BTN",
)
# Returns: {status, progress, strategy: [{action, frequency, ev}]}
```

### Quick diagnostic commands

```bash
# API health
curl -s http://localhost:8003/api/v1/health

# Solver health
curl -s http://localhost:8003/api/v1/solver/health

# Submit a solve
curl -s -X POST http://localhost:8003/api/v1/solver/solve \
  -H 'Content-Type: application/json' \
  -d '{"board":"Kd7h2c","pot_size":100,"iterations":500,"street":"river","position":"BTN"}'

# Public
curl -s https://wiz.codeovertcp.com/api/v1/health
```

### 21 routes now

Current pages (all return 200):
`/study`, `/equity`, `/play`, `/practice`, `/plo`, `/analyze`, `/analyze/hands`, `/analyze/leaks`, `/analyze/viewer`, `/icm`, `/courses`, `/spots`, `/train`, `/train/review`, `/strategies`, `/strategy`, `/double-board`, `/bomb-pot`, `/omaha`

### Nav tabs

| Tab | Route | Status |
|-----|-------|--------|
| Hold'em | `/equity` | ✅ |
| PLO NEW | `/plo` | ✅ |
| Play | `/play` | ✅ Built June 9 |
| 🎓 Study | `/study` | ✅ Reference-adapted |
| Practice | `/practice` | ✅ Built June 9 |
| Analyze | `/analyze` | ✅ Reference-adapted |

### Start commands (current — HOST deployment)

```bash
# gRPC Solver (on host)
cd /home/sean/gto-wizard-clone
nohup /home/sean/hermes-apps-venv/bin/python3 -m apps.solver.server > /tmp/solver-grpc.log 2>&1 &

# API backend (on host, from apps/api/ with PYTHONPATH='..')
cd /home/sean/gto-wizard-clone/apps/api
PYTHONPATH='..' nohup /home/sean/hermes-apps-venv/bin/uvicorn main:app --host 0.0.0.0 --port 8003 --log-level warning > /tmp/gto-api.log 2>&1 &

# Frontend (host-managed, auto-restarts)
# Just build and the systemd process picks it up:
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 "
cd /home/sean/gto-wizard-clone/apps/web
export PATH=\$HOME/.hermes/node/bin:\$PATH
export NEXT_PUBLIC_API_URL=http://localhost:8003
npx next build && pkill -9 -f next-server  # auto-restarts
"

# Cloudflare tunnel (host-managed via systemd)
```

See `devops/gto-wizard-deployment` skill for the full deployment procedure.

## OVERVIEW (stale below — kept for reference, paths/ports may be wrong)

```bash
# API backend
cd /workspace/gto-wizard-clone
PYTHONPATH=/workspace/gto-wizard-clone/apps/api:/workspace/gto-wizard-clone \
  /app/venv/bin/uvicorn apps.api.main:app --host 0.0.0.0 --port 8002

# Frontend (background processes need explicit PATH)
export PATH="/home/hermeswebui/.hermes/home/.local/bin:$PATH"
cd /workspace/open-lovable && PORT=8555 ./node_modules/.bin/next start -p 8555
```

**Critical — background process PATH**: Background processes do NOT inherit PATH. Always use `export PATH=...` or absolute paths.

**Critical — killing zombies**: `fuser -k PORT/tcp` first. If that fails, use /proc inode matching. Best fix: use a fresh port and update tunnel config.

## Lint & Format Maintenance

Ruff may need installing first: `.venv/bin/pip install ruff` or `uv pip install ruff`.

Before starting any work, always check for pre-existing dirty state and clean it:

```bash
# Check for pre-existing uncommitted changes
git status --short

# If there are pre-existing changes unrelated to your work (e.g., leftover format sweeps),
# restore them to keep commits clean:
git checkout -- .

# Or stash if the changes might be important:
git stash push -m "pre-existing dirty state before maintenance"
```

**Regular ruff maintenance sequence (safe for auto-continue cron jobs):**

```bash
# 0. Check for pre-existing dirty state first
git status --short
# If dirty from previous auto-runs: git checkout -- . or git stash

# 1. Full-project auto-fix sweep
python -m ruff check --fix .

# 2. Handle post-fix F821 (undefined name) — these are runtime bugs, not auto-fixable
python -m ruff check . --select F821
# Common patterns that need manual fixes:
#   - Missing `timezone` in `from datetime import datetime, timezone`
#   - Missing `import os` when `os.path` or `os.environ` is used
#   - String forward-references like `"TexasHoldEm"` → add `# noqa: F821`
#   - Missing `import sys` when `sys.path` is used
# Patch each missing import, noqa each valid forward-ref, then re-check.

# 3. Format source files
python -m ruff format .

# 4. Verify remaining issues — should be E402/E701/E741/E712/F403 only (style)
python -m ruff check . --statistics

# 5. Full test suite
python -m pytest packages/poker-core/tests/ -q
python -m pytest apps/solver/tests/ -q

# 6. Commit
git add -A
git commit -m "auto: T2/T3 — ruff --fix + F821 manual fixes: <summary>"

**Pitfalls:**
- `ruff check --select F401 --fix` is the safest-first pass (removes unused imports only, zero risk)
- After `ruff check --fix` on the full monorepo, **always** run `ruff check . --select F821` — the auto-fixer frequently removes imports that other code paths still need, creating F821 errors
- `ruff format --check` before applying to see what would change
- Ruff may not be installed in the venv — install first with `.venv/bin/pip install ruff` or `uv pip install ruff`
- `ruff check` on the entire monorepo includes `apps/web/` (TypeScript/TSX) and `apps/api/prisma/` (Python-protected dirs) which ruff skips silently — the glob is safe
- `pip list --outdated` is slow (times out at 15s) — use `uv pip list --outdated` instead (2s) for dependency checks
- **Check git status first**: Pre-existing uncommitted formatting changes from previous runs are common. Always restore unrelated changes before committing your work.
- **test_ prefix trap**: Solver source modules may have utility/demo functions named `test_*()` (e.g. `test_flop_solve`, `test_create_turn_state`). These get collected as pytest tests when imported into test files, inflating the count and causing `PytestReturnNotNoneWarning`. If test counts drop between runs (e.g. 212→208 solver), this is the cause. Rename to `demo_*` and remove unused imports from test files.
- **F821 forward-refs in nodes.py**: The `GameTreeBuilder` class uses string-typed forward references (`"TexasHoldEm"`, `"GameState"`) which are valid PEP 484 patterns. Ruff F821 flags them. Suppress with `# noqa: F821` on the annotation line — never import `TexasHoldEm` or `GameState` at module level (causes circular imports).

## Tests

**Always run the three suites separately:**

```bash
# Poker-core (357 tests)
PYTHONPATH=/tmp/gto-wizard-clone/packages/poker-core/src \
  .venv/bin/pytest packages/poker-core/tests/ -q

# Solver (208 tests)
PYTHONPATH=/tmp/gto-wizard-clone/packages/poker-core/src:/tmp/gto-wizard-clone/apps/solver \
  .venv/bin/pytest apps/solver/tests/ -q

# API (9 tests)
PYTHONPATH=/tmp/gto-wizard-clone/apps/api:/tmp/gto-wizard-clone \
  .venv/bin/pytest apps/api/tests/ -q
```

**Total: ~574 tests. All must pass before declaring work complete.**

**Pitfall — test_ prefix in non-test modules:** Functions named `test_*()` in solver source modules (not test files) get collected as pytest tests when imported into test files. This causes `PytestReturnNotNoneWarning` and inflates the test count. If you see fewer tests passing than expected (e.g. 208 instead of 212 in solver), check whether utility/demo functions in `cfr/flop_solver.py`, `cfr/turn_solver.py` etc. have `test_` prefix. Rename them to `demo_*` and update the test file imports to remove the unused imports. Verify with `-W "default::pytest.PytestReturnNotNoneWarning"`.

## Cloudflare Tunnel

- **Email:** `seanos1a@gmail.com`
- **Key:** `4551f6bda4835ee658c81221ee8783c9e7af3`
- **Zone ID:** `a0dc1c2d5a810fabb43cb596a7e4b322`
- **Account ID:** `fd4058c7aa1da2cb3ec2f2c9f028c022`

See `references/cloudflare-tunnel-remote-config-override.md` for the remote config override pattern (named tunnels have TWO config sources; remote API config overrides local YAML).

## Spec-First Development (THE Workflow)

1. **DISCOVER**: Research target product, download 50+ reference images
2. **SPEC**: Write comprehensive PRD at `/workspace/gto-wizard-prd.md`
3. **FIX BY PRIORITY**: P0 first, all P0 must pass QA before P1
4. **BUILD STRUCTURE FIRST**: Layout hierarchy before colors
5. **APPLY TOKENS SECOND**: Design system after structure matches
6. **QA PIPELINE**: Puppeteer pipeline, 0 console errors
7. **VERIFY PUBLIC URL**: Curl tunnel URL after deploy

**Consult the PRD before every feature commit. Never build a feature not in the PRD.**

## "Proceed" / "keep going" = Autonomous Execution

When the user says "proceed," "complete all tasks," or "keep going until done":
- Execute autonomously — do NOT stop to explain
- Do NOT ask for confirmation
- Complete TO COMPLETION — passing all QA checks
- Only notify when entire goal is achieved or blocked

## Design System

**File**: `/workspace/open-lovable/styles/gto-tokens.ts`

| Token | Hex | Usage |
|-------|-----|-------|
| bg | `#1a1a1a` | Page background |
| bgElevated | `#2a2a2a` | Card surfaces |
| accent | `#00C9A7` | Primary buttons, active tabs |
| border | `#3a3a3a` | Card borders |
| textSecondary | `#aaaaaa` | Body text |
| textTertiary | `#888888` | Labels |

**Always use explicit hex values** — never Tailwind semantic classes for GTO pages.

**13×13 matrix requires Tailwind extension:**
```typescript
gridTemplateColumns: { '13': 'repeat(13, minmax(0, 1fr))' },
gridTemplateRows: { '13': 'repeat(13, minmax(0, 1fr))' },
```

## Key Pitfalls

### Spec First, Code Second
Frustration = process gap, not a color tweak. Fix the process first (update PRD), THEN fix the code.

### Two SQLAlchemy Base Classes
API returns `{strategies:[{...}], count:0}` not raw arrays. Frontend must handle both:
```typescript
const data = await r.json();
const items = Array.isArray(data) ? data : data?.strategies || data?.courses || data?.spots || [];
```

### `.turbo/` cache
`turbo` and `nx` cache directories (`.turbo/cache/`, `node_modules/.cache/turbo/`) are NOT in `.gitignore`. After running `git add -A`, check that build cache artifacts aren't staged. Either add `.turbo/` to `.gitignore` or use `git add -u` (only tracked files) instead of `git add -A`.

### Open Lovable is THE Framework
The delivered product is GTO Wizard Clone, not Open Lovable's AI builder. Root URL redirects to `/gto/equity`.

### Zombie Process Management
`fuser -k PORT/tcp` first. Best fix: use fresh port + update tunnel config. Don't fight zombies.

### Hardcoded Path Anti-Pattern
### Hardcoded Path Anti-Pattern

Solver source files historically contained hardcoded `/tmp/gto-wizard-clone/` paths. **DO NOT replace with another hardcoded path** — use dynamic relative path computation instead. The repo lives at different paths on container and host, so hardcoded paths always break one environment.

**Fix pattern** — for files inside `apps/solver/SUBDIR/` (cfr/, tests/, games/, strategy/):
```python
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
```

For files at solver root: remove the insert. For poker-core: remove entirely (gto-poker is pip-installed).

**After fixing:** check each file for missing `import os` if the file now uses `os.path`. All 18 files were fixed in commit `b9b39ed`.

### Solver Performance
Hand evaluation and CFR tree traversal are the main bottlenecks. Key optimizations already applied:
- **Fast hand evaluator**: `packages/poker-core/src/gto_poker/hand_fast.py` — use `compare_hands_fast()` instead of `HandEvaluator.compare()` (160x faster 7-card compare)
- **Tuple infoset keys**: `GameState.infoset_key()` returns tuple instead of string (eliminates 500+ str.join calls per solve)
- See `references/solver-performance-optimization.md` for full details, benchmarks, and remaining opportunities.

**Patching pitfall**: Multiple `patch` operations on the same file can introduce duplicate `import` statements. Always read the file after patching to verify no duplicates.

### Reference Screenshots
50+ real GTO Wizard screenshots at `/workspace/gto-wizard-references/`. Use `vision_analyze` before building.

## All 14 Pages

| Route | Page | Group |
|-------|------|-------|
| `/gto/equity` | Equity Calculator | STUDY |
| `/gto/solver` | MCCFR Solver | STUDY |
| `/gto/strategy` | Strategy Viewer | STUDY |
| `/gto/icm` | ICM Calculator | STUDY |
| `/gto/training` | Training / Quizzes | PRACTICE |
| `/gto/courses` | Course Browser | PRACTICE |
| `/gto/spots` | Community Spots | PRACTICE |
| `/gto/hands` | Hand History Manager | ANALYZE |
| `/gto/leaks` | Leak Analysis | ANALYZE |
| `/gto/plo4` | PLO4 Calculator | MORE |
| `/gto/omaha` | Omaha Variants | MORE |
| `/gto/double-board` | Double Board | MORE |
| `/gto/bomb-pot` | Bomb Pot | MORE |
| `/gto/auth` | Login / Register | — |

## Crons

When setting up or updating crons for GTO Wizard, observe these rules:

- **Model:** Always use `@opencode-go:deepseek-v4-flash` for ALL GTO-related cron jobs (user's explicit preference). Never default to openrouter models for poker work.
- **Delivery:** Use `deliver: local` (cron output stays in the scheduler, not pushed to chat).
- **Repeat:** Set a finite repeat count (e.g. `repeat: 3`) for overnight jobs so they don't run forever.
- **SSH commands:** All host-side commands must use `ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 "command"`.
- **QA before update:** Run the comprehensive QA checklist (see `devops/gto-wizard-deployment` skill's `references/comprehensive-qa-2026-06-11.md`) to find issues, THEN update cron prompts to include fixes.

### Standard Overnight Rotation

| Cron | Purpose | Schedule (UTC) | Sydney | Model |
|------|---------|----------------|--------|-------|
| **DB seed** | Fix seed scripts, populate quiz spots/courses | `0 */3 * * *` × 3 | 01:00, 04:00, 07:00 | `@opencode-go:deepseek-v4-flash` |
| **Build + deploy** | Pull latest, rebuild frontend, restart API | `30 */3 * * *` × 3 | 01:30, 04:30, 07:30 | `@opencode-go:deepseek-v4-flash` |
| **QA audit** | Full page/API/solver audit with auto-recovery | `0 0,2,4,6 * * *` × 4 | 10:00, 12:00, 14:00, 16:00 | `@opencode-go:deepseek-v4-flash` |

See `devops/gto-wizard-deployment` skill for full deployment procedures, troubleshooting patterns, and the comprehensive QA checklist.
