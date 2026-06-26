# Deep Codebase Extraction for Technical Analysis

Extract specific engineering facts from a codebase for analytical output (resume bullets, architecture docs, performance reports, security audits).

## When to Use

Trigger when the user asks for:
- Deep technical details about a project (metrics, trade-offs, algorithms)
- Resume/interview bullet points built from real code
- Architecture documentation with specific implementation details
- Performance or complexity claims that must be code-grounded

## File Selection Strategy by Project Type

### Multi-package Monorepo (Node + Python + Go)

Priority order — scan in this sequence:

1. **CI/CD** — `.github/workflows/*.yml` — build parallelism, test matrix, deployment gates, cache strategy
2. **Dockerfiles** — multi-stage build patterns, base images, layer optimization, final image size
3. **Package manifests** — `package.json`, `pyproject.toml`, `go.mod` — dependencies, scripts, entrypoints
4. **Entrypoint scripts** — `scripts/*.py`, `scripts/*.sh` — watchdog, health checks, bootstrap logic
5. **Core domain packages** — `packages/*/src/` or `packages/*/*/` — business logic, agents, routing
6. **Backend server** — `src/index.ts`, `src/routes/*.ts` — concurrency patterns, Socket.io usage
7. **Agent/LLM integration** — `aie_client.py`, `event_emitter.py`, `agent_hook.py` — async patterns, event types
8. **Observability** — `logger.py`, `drift.py`, `events.py` — data structures, algorithmic complexity
9. **Frontend** — `App.tsx`, key components — SSE/Socket.io consumption, state management, ring buffers

### API/Backend Service

1. **Router/dispatcher** — `server.py`, `router.ts`, route handlers
2. **Concurrency primitives** — locks, queues, connection pools
3. **Error handling** — retry logic, circuit breakers, fallback paths
4. **Config/environment** — env var usage, secrets patterns

### Key Patterns to Identify

| Pattern | What to Look For | Why It Matters |
|---------|-------------------|----------------|
| Watchdog/health | SIGTERM handlers, polling intervals, fail thresholds | System resilience, restart reliability |
| TCP/port detection | `createConnection`, socket timeouts, deferred spawns | Race conditions in bootstrap |
| Async locks | `asyncio.Lock()`, `RLock()`, `threading.Lock()` | Concurrency correctness |
| Fire-and-forget | `try/except pass`, no-await emit patterns | Resilience vs. blocking |
| Ring buffers | Slice to N on prepend (`slice(0, 200)`) | Memory boundedness |
| Lifecycle hooks | `before_execute_tools`, `after_iteration` hook registration | Observability instrumentation points |
| Multi-stage Docker | Sequential `FROM` stages, `--from=X` copies | Image size optimization |
| Session locks | `session_locks = {}`, per-user async locks | Multi-tenant concurrency |

## Algorithmic Complexity Extraction

- **O(1) lock acquisition** per event in async logger → no contention if events are independent
- **O(n) aggregation** over event history → drift scoring, token counting
- **O(log n) lookup** → session key maps, config resolution
- **O(n) iteration** per tool call → argument parsing, blueprint injection

State which one applies and why it matters for the specific claim.

## Grounding Quantifiable Claims

Before writing a bullet with a number, verify:
- "100% elimination" → has the system actually run without manual intervention long enough to claim this?
- "~60% reduction" → measure vs. a naive baseline (e.g., single-stage build with all toolchains)
- "O(1) per tool call" → confirm the async lock is the only per-call overhead
- Specific timeouts (500ms, 700ms) → verify from actual source, not assumption

## Verbatim Code Patterns

### Async JSONL logger with asyncio.Lock
```python
class AIELogger:
    def __init__(self, log_path: str):
        self._lock = asyncio.Lock()

    async def log(self, event: dict) -> None:
        line = json.dumps(event) + "\n"
        async with self._lock:
            with open(self.log_path, "a") as f:
                f.write(line)
```
→ O(1) per event, no blocking on I/O for the caller

### Fire-and-forget with local fallback
```python
async def log(self, event: dict) -> None:
    # Always write locally first
    with open(self.log_path, "a") as f:
        f.write(line)
    # Then try remote, silently fail
    try:
        async with aiohttp.post(url, json=payload) as resp:
            pass
    except Exception:
        pass  # silent — agent never blocks on observability
```

### Ring buffer (bounded memory)
```typescript
// Frontend: keep max 200 events, display last 50
setEvents(prev => [{ type: '__task_start', ... }, ...prev].slice(0, 200))
```

### TCP port probe with deferred spawn
```typescript
// Check if external process already holds the port
const sock = createConnection(PORT, HOST)
sock.on('connect', () => { sock.destroy(); nanobotReady = true })
sock.on('error', () => { nanobotReady = false })
sock.setTimeout(500)
setTimeout(() => { try { sock.destroy() } catch {} }, 600)

// Spawn only if port was free
setTimeout(startNanobotSidecar, 700)
```
→ Prevents EADDRINUSE on restart when external process preempts

### Health check watchdog
```python
POLL_INTERVAL = 30  # seconds
FAIL_THRESHOLD = 3  # consecutive failures before restart

for _ in range(POLL_INTERVAL):
    if shutdown_requested:
        break
    time.sleep(1)  # 1s granularity — restart unblocks within 1 poll cycle
```
→ Graceful SIGTERM handling, 1s restart unblock granularity
