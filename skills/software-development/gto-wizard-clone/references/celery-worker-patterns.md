# Celery Worker Patterns — GTO Wizard Clone

## Circular Import Pattern

The #1 gotcha: `celery_app.py` imports `tasks.py` via `include=[]`, but `tasks.py` needs `app` from `celery_app.py`.

**Solution**: Use `shared_task` decorators + lazy import:

```python
# tasks.py — module level
from celery import shared_task
from apps.worker.celery_app import get_progress_channel  # OK — no circular dep

@shared_task(name="solver.solve_spot", queue="solver", max_retries=2)
def solve_spot(params):
    ...

@shared_task(name="solver.submit_solve", queue="default")
def submit_solve(params):
    # Lazy import — only needed inside this function
    from apps.worker.celery_app import celery_app
    celery_app.send_task("solver.solve_spot", args=[params])
```

**Why this works**: `shared_task` registers with `current_app` at decoration time. The `celery_app` object is fully created by the time `include=[]` triggers the import. Only `send_task()` needs the actual `celery_app` reference, which is imported lazily inside the function body.

## Worker Dockerfile Pattern

Worker needs `packages/poker-core` and `apps/solver` at runtime. Install BEFORE copying worker source:

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

**Order matters**: If you copy `apps/worker/` before installing `poker-core`, the worker can't import `gto_poker.double_board` etc.

## Redis → WebSocket Bridge

Three components:

1. **Worker** publishes progress to `solver:progress:{job_id}` Redis channel
2. **RedisService** subscribes via `psubscribe` to `solver:progress:*` pattern
3. **ProgressBridge** forwards messages to WebSocketManager via `asyncio.run_coroutine_threadsafe`

```python
# progress_bridge.py
class ProgressBridge:
    _instance = None
    _lock = threading.Lock()  # CLASS-LEVEL lock (not instance)

    def _on_progress(self, data):
        job_id = data.get("job_id")
        if not job_id or not self._loop:
            return
        asyncio.run_coroutine_threadsafe(
            self._ws_manager.handle_solver_progress(job_id, data), self._loop)
```

**Wiring in main.py**:
- Startup: `ProgressBridge.register()` after `init_redis()`
- Shutdown: `ProgressBridge._instance.stop()`

**RedisService pattern subscribe**:
- `subscribe_to_progress(job_id="*")` → pattern channel `solver:progress:*`
- `_listen_for_updates()` uses `psubscribe` for patterns, `subscribe` for exact
- Handles both `message` and `pmessage` types
- Falls back to pattern matching for callbacks when exact channel not found

## Task Routing

Tasks are routed to 3 queues:
- `solver` (10 tasks): CFR solving, variant equity, push/fold charts
- `analysis` (3 tasks): Batch HH import, leak detection, ICM batch
- `default` (2 tasks): Status checks, cleanup

Worker must specify: `-Q solver,analysis,default`

## Retry/Backoff Pattern

All long-running tasks use `max_retries=2` with `SoftTimeLimitExceeded` triggering retry with halved work (iterations/samples). This handles the case where a solve is too big for the time limit — retry with fewer iterations rather than failing outright.

## Event Loop in Celery Tasks

**NEVER** create `asyncio.new_event_loop()` in Celery worker's main thread (deadlocks with prefork pool). For async DB operations in tasks, use `ThreadPoolExecutor(max_workers=1)` with a dedicated event loop per call.

## Progress Publishing

Publish at key milestones: 0% (init), 5% (building state), every ~5% during solving, 90% (finalizing), 100% (complete). Each publish updates both the Redis pub/sub channel and the `job:status:{job_id}` cache key.
