# Celery + Redis Pub/Sub → WebSocket Bridge Pattern

Realtime progress streaming from background tasks to browsers.

## Problem

Celery tasks run for minutes (CFR solver, ML training, report generation).
Browser needs live progress updates. HTTP polling wastes resources.
gRPC is wrong for browsers — requires grpc-web proxy.

## Architecture

```
Browser              API (FastAPI)           Worker (Celery)         Redis
  │                      │                       │                    │
  ├─ POST /solve ──────→ │                       │                    │
  │  ← job_id ──────────┤                       │                    │
  │                      ├─ submit_solve() ────→ │                    │
  │                      │                       ├─ publish_progress ─┤
  │                      │                       │  (channel:         │
  │                      │                       │   solver:progress  │
  │                      │                       │   :{job_id})       │
  │                      │                       │                    │
  ├─ WS /ws/{id} ──────→ │                       │                    │
  │                      ├─ redis.subscribe() ──────────────────────→│
  │                      │←── msg ←─────────────────────────────────┤
  │←── progress JSON ────┤                       │                    │
  │                      │                       ├─ 100% complete ──→│
  │←── complete ─────────┤                       │                    │
  │  WS closes           │                       │                    │
```

## Worker Side (Celery Task)

```python
import json, time, os
from celery import shared_task

def _get_redis_client():
    """Env-based Redis with fakeredis fallback."""
    redis_url = os.environ.get("REDIS_URL", "")
    if redis_url:
        try:
            import redis as r
            c = r.from_url(redis_url, decode_responses=True)
            c.ping()
            return c
        except Exception:
            pass
    try:
        import fakeredis
        return fakeredis.FakeRedis(decode_responses=True)
    except ImportError:
        pass
    # in-memory stub fallback
    from apps.api.services.redis_service import _InMemoryStub
    return _InMemoryStub()

def publish_progress(job_id, progress, status, extra=None):
    """Publish progress to Redis channel and cache."""
    client = _get_redis_client()
    msg = {
        "type": "solve:progress",
        "job_id": job_id,
        "progress": progress,
        "status": status,
        "timestamp": time.time(),
    }
    if extra:
        msg.update(extra)
    client.publish(f"solver:progress:{job_id}", json.dumps(msg))
    client.set(f"job:status:{job_id}", json.dumps(msg), ex=86400)

@shared_task(bind=True, name="solver.solve_spot")
def solve_spot(self, params):
    job_id = params.get("job_id")
    publish_progress(job_id, 0, "running", {"stage": "initializing"})
    # ... do work, call publish_progress() at key milestones ...
    publish_progress(job_id, 100, "complete", {"stage": "complete"})
    # Cache final result too
    client = _get_redis_client()
    client.set(f"job:result:{job_id}", json.dumps(result), ex=86400)
    return result
```

## API WebSocket Side (FastAPI)

```python
@router.websocket("/ws/{job_id}")
async def solver_websocket(ws: WebSocket, job_id: str):
    await ws.accept()
    redis_svc = get_redis_service()

    # Send cached initial status
    cached = redis_svc.get_job_status(job_id)
    if cached:
        await ws.send_json({"type": "status", "job_id": job_id, **cached})
        if cached.get("status") in ("complete", "error"):
            await ws.close()
            return

    # Subscribe to Redis pub/sub channel
    pubsub = redis_svc.pubsub_client.pubsub()
    pubsub.subscribe(f"solver:progress:{job_id}")

    try:
        while True:
            msg = pubsub.get_message(timeout=0.5)
            if msg and msg["type"] == "message":
                data = json.loads(msg["data"])
                await ws.send_json(data)
                if data.get("status") in ("complete", "error"):
                    break
            try:
                txt = await asyncio.wait_for(ws.receive_text(), timeout=0.1)
                if txt == "ping":
                    await ws.send_json({"type": "pong"})
                elif txt == "unsubscribe":
                    break
            except asyncio.TimeoutError:
                pass
    finally:
        pubsub.unsubscribe()
        pubsub.close()
        await ws.close()
```

## Why Not gRPC for Browser-Facing Patterns

- Browsers can't speak HTTP/2 bidirectional streaming natively
- grpc-web proxy (envoy) adds operational complexity
- Celery already handles async execution, Redis pub/sub handles broadcasting, WebSocket handles delivery
- gRPC adds a 4th component (proto compiler, generated stubs, separate port) for zero gain

**When gRPC makes sense:** Service-to-service communication *within* the backend where both sides are Python/TypeScript. Not for browser-facing patterns.

## Docker Compose Notes

- Put `REDIS_URL=redis://redis:6379/0` in all services that need it (api, worker)
- Never hardcode `localhost` in worker tasks — it won't resolve in Docker
- Worker Dockerfile must contain all import paths its tasks need (copy full monorepo or restructure imports)
