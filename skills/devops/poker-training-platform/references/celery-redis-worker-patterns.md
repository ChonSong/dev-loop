# Celery + Redis Worker Patterns (2026-07)

Concrete patterns from implementing the GTO Wizard Clone worker system.

## shared_task Circular Import Fix

**Problem:** `celery_app.py` has `include=["apps.worker.tasks"]`, but `tasks.py` needs `app` from `celery_app.py`. Circular import.

**Solution:**
```python
# celery_app.py
celery_app = Celery("gto_solver", broker=..., backend=...)
app = celery_app  # backward-compat alias

# tasks.py — NO import of app/celery_app at top level
from celery import shared_task

@shared_task(bind=True, name="solver.solve_spot", queue="solver")
def solve_spot(self, params):
    ...

# Lazy import only where send_task() is needed
def submit_solve(params):
    from apps.worker.celery_app import celery_app
    celery_app.send_task("solver.solve_spot", args=[params])
```

## Redis → WebSocket Progress Bridge

Three-component pattern:

1. **Worker** calls `publish_progress(job_id, pct, status)` → Redis pub/sub channel `solver:progress:{job_id}`
2. **RedisService** uses `psubscribe("solver:progress:*")` to listen to all job channels
3. **ProgressBridge** forwards messages to `WebSocketManager.broadcast_to_job()` via `asyncio.run_coroutine_threadsafe`

Key files:
- `apps/worker/tasks.py` — `publish_progress()` helper
- `apps/api/services/redis_service.py` — `subscribe_to_progress(job_id="*")` + `_listen_for_updates()` with psubscribe
- `apps/api/services/progress_bridge.py` — `ProgressBridge` singleton
- `apps/api/main.py` — bridge starts on startup, stops on shutdown

## ProgressBridge Class-Level Lock

**Gotcha:** `_lock = threading.Lock()` in `__init__` can't be accessed as `cls._lock` in a `@classmethod`. Must be a class variable:

```python
class ProgressBridge:
    _instance = None
    _lock = threading.Lock()  # class-level, NOT in __init__

    @classmethod
    def register(cls):
        with cls._lock:
            ...
```

## Multi-Queue Routing

```python
task_routes = {
    "solver.*": {"queue": "solver"},     # 10 tasks: CFR solves
    "analysis.*": {"queue": "analysis"},  # 3 tasks: batch HH, leaks, ICM
    "maintenance.*": {"queue": "default"}, # 2 tasks: cleanup, status
}
```

Worker: `celery -A app worker -Q solver,analysis,default --concurrency=4`
Beat: `celery -A app beat --loglevel=info` (separate service)

## Retry/Backoff on SoftTimeLimitExceeded

```python
@shared_task(bind=True, name="solver.solve_spot", queue="solver",
           max_retries=2, default_retry_delay=10)
def solve_spot(self, params):
    try:
        # ... CFR solve ...
    except SoftTimeLimitExceeded:
        retry_params = dict(params)
        retry_params["iterations"] = max(100, iterations // 2)
        if self.request.retries < self.max_retries:
            raise self.retry(args=[retry_params])
        raise
```

## Strategy Storage — Async in Celery Worker

**Never** create `asyncio.new_event_loop()` in Celery's main thread (deadlocks with prefork pool). Use `ThreadPoolExecutor`:

```python
def store_strategy_if_available(...):
    def _store():
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(storage.store_strategy(...))
        finally:
            loop.close()
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        future = ex.submit(_store)
        future.result(timeout=30)
```

## Variant Task Pattern

Each poker variant gets a dedicated Celery task for explicit routing:

| Task | Variant | Evaluator |
|------|---------|-----------|
| `solver.solve_spot` | NLH | HandEvaluator |
| `solver.solve_flop_spot` | NLH flop | HandEvaluator |
| `solver.solve_turn_spot` | NLH turn | HandEvaluator |
| `solver.solve_plo4_spot` | PLO4 | PLO4Evaluator |
| `solver.solve_omaha_spot` | Omaha Hi/Lo | PLO4Evaluator + split pot |
| `solver.solve_shortdeck_spot` | Shortdeck | Modified rankings |
| `solver.solve_double_board_equity` | Double Board PLO | DoubleBoardEquity MC |
| `solver.solve_bomb_pot_equity` | Bomb Pot | BombPotGameModel MC |

## Worker Dockerfile

```dockerfile
FROM python:3.12-slim
COPY packages/poker-core ./packages/poker-core
RUN pip install -e ./packages/poker-core
COPY apps/solver ./apps/solver
RUN pip install -e ./apps/solver
COPY apps/api ./apps/api
COPY apps/worker/ ./apps/worker/
CMD ["celery", "-A", "apps.worker.celery_app", "worker",
     "--loglevel=info", "--concurrency=4",
     "-Q", "solver,analysis,default"]
```

Key: install monorepo packages (poker-core, solver) as editable BEFORE copying worker source.
