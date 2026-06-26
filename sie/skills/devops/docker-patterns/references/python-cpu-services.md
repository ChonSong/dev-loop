# Python CPU-Intensive Services — Docker Patterns for gRPC Solver

## The Problem

The GTO Wizard Clone solver engine (`apps/solver/`) is CPU-intensive Python code using:
- NumPy (matrix operations)
- Numba JIT (hot path compilation)
- gRPC service (separate from FastAPI API)

Standard Python Docker patterns don't account for JIT compilation overhead and Numba-specific requirements.

## Resolved Architecture: Dual-Path (Celery + gRPC)

The API communicates with the solver via **two paths** — each for a different purpose:

| Path | Use | Who Calls |
|------|-----|-----------|
| **Celery (async)** | Long-running CFR solve jobs | FastAPI → `apps.worker.tasks` → Redis broker → Worker |
| **gRPC (sync)** | Fast ICM calcs, strategy lookups, health checks | FastAPI → `solver_client.py` → gRPC server |

The frontend talks to the API over REST/WebSocket. The API talks to the solver over gRPC (sync) or Celery (async). The frontend never touches gRPC directly.

```
Browser → REST/WS → FastAPI API ─┬─ gRPC (sync)  → Solver gRPC server (ICM, strategy, health)
                                 └─ Celery (async) → Worker → CFR engine (solve jobs)
```

**Key insight:** ICM runs locally in the API as a fallback (`gto_poker.icm`) when gRPC is unavailable. The gRPC call takes ~10-30s for Monte Carlo sims, so the local fallback is actually faster for simple cases.

## Docker Pattern for Numba-Accelerated Python Services

```dockerfile
FROM python:3.12-slim

# Install system deps FIRST (needed for C extensions, gRPC, Numba's LLVM)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    cmake \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy monorepo packages first (layer caching)
COPY packages/poker-core ./packages/poker-core
RUN pip install -e ./packages/poker-core

# Install solver dependencies
COPY apps/solver/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy solver source
COPY apps/solver/ ./apps/solver/

EXPOSE 50051

# IMPORTANT: Use start_grpc_server.py, NOT "python -m solver.service"
# There is no __main__.py in solver/. The correct entrypoint is the script.
WORKDIR /app/apps/solver
CMD ["python", "start_grpc_server.py", "--port", "50051"]
```

## Requirements

The solver requirements (`apps/solver/requirements.txt`) should include:
```
grpcio>=1.60
grpcio-tools>=1.60
numpy>=2.0
numba>=0.60
redis>=5.0
```

The API requirements (`apps/api/requirements.txt`) should also include `grpcio` and `grpcio-tools` since it acts as a gRPC client.

## gRPC Client Pattern (API Side)

```python
# apps/api/services/solver_client.py

import os, logging, grpc

SOLVER_GRPC_URL = os.environ.get("SOLVER_GRPC_URL", "solver:50051")

def _lazy_import_stub():
    """Import protobuf stubs — works in Docker and monorepo layouts."""
    import sys
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    for proto_path in [
        os.path.join(base, "apps", "solver", "proto"),     # monorepo
        "/app/apps/solver/proto",                            # Docker absolute
    ]:
        if os.path.exists(os.path.join(proto_path, "solver_pb2.py")):
            if proto_path not in sys.path:
                sys.path.insert(0, proto_path)
            break
    import solver_pb2, solver_pb2_grpc
    return solver_pb2, solver_pb2_grpc

@contextmanager
def solver_client():
    pb2, stub_cls = _lazy_import_stub()
    channel = grpc.insecure_channel(SOLVER_GRPC_URL, [
        ("grpc.max_receive_message_length", 50 * 1024 * 1024),
    ])
    stub = stub_cls.SolverServiceStub(channel)
    try:
        yield pb2, stub
    except grpc.RpcError as e:
        logger.error(f"Solver gRPC error: {e.code()} - {e.details()}")
        raise
```

## docker-compose.yml Pattern

```yaml
services:
  solver:
    build:
      context: .
      dockerfile: apps/solver/Dockerfile
    ports:
      - "50051:50051"
    environment:
      REDIS_URL: redis://redis:6379/0
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/gto_wizard
      GRPC_PORT: "50051"
      GRPC_MAX_WORKERS: "10"
    depends_on:
      redis:
        condition: service_healthy
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "python", "-c",
              "import grpc; channel=grpc.insecure_channel('localhost:50051'); "
              "stub=grpc.channel_ready_future(channel); stub.result(timeout=5)"]
      interval: 15s
      timeout: 10s
      retries: 5
      start_period: 30s
    deploy:
      resources:
        limits:
          cpus: '4'       # CFR is CPU-bound
          memory: 4G

  api:
    build:
      context: .
      dockerfile: apps/api/Dockerfile
    depends_on:
      solver:
        condition: service_healthy   # API waits for solver to be ready
    environment:
      SOLVER_GRPC_URL: solver:50051  # DNS name = service name in Docker network
```

## Key Pitfalls

| Pitfall | Fix |
|---------|-----|
| `CMD ["python", "-m", "solver.service"]` fails — no `__main__.py` | Use `CMD ["python", "start_grpc_server.py", "--port", "50051"]` |
| `COPY /tmp/PokerHandEvaluator` in Dockerfile not available at build time | Remove it; install phevaluator from PyPI or inline |
| gRPC channel not resolving `solver:50051` | Both services must be on the same Docker network; use service name as DNS |
| API starts before solver is ready | Add `depends_on: solver: condition: service_healthy` |
| Proto files not found in API container | COPY `apps/solver/proto/` into API image |
| ICM call times out (100k sims) | Use 10k for API calls with gRPC, 100k+ for batch Celery jobs |
| Singleton gRPC channel across requests | Create channel once, reuse per-request stubs |
| ICM calc is slow over gRPC but fast locally | Add local fallback: try gRPC first, catch exception, use `gto_poker.icm` |
| Sibling subagents writing to same docker-compose.yml | Re-read file before patching; use depends_on with healthcheck to serialize |

## Endpoints Exposed by the Solver gRPC Server

| RPC | Request | Response | Typical Latency |
|-----|---------|----------|-----------------|
| `HealthCheck` | service name | healthy, status, details | <100ms |
| `CalculateICM` | stacks, prizes, n_simulations | per-player equity, bubble factor | 5-30s |
| `GetICMForSpot` | stacks, prizes, position, hand | equities, bubble factors, recommendation | 5-30s |
| `GetStrategy` | game_type, board, street, position | strategy JSON (push/fold charts) | <1s (cached) |
| `SubmitSolve` | game params + CFR config | job_id, status | <100ms |
| `StreamProgress` | job_id | stream of ProgressUpdate | Long-running |

## Generate gRPC Stubs

```bash
python -m grpc_tools.protoc \
    -I./apps/solver/proto \
    --python_out=./apps/solver/proto \
    --grpc_python_out=./apps/solver/proto \
    --pyi_out=./apps/solver/proto \
    ./apps/solver/proto/solver.proto
```

Output goes to `apps/solver/proto/` (same dir as .proto). The generated files (`solver_pb2.py`, `solver_pb2_grpc.py`) are committed to git — no need to regenerate at build time.

## Testing Locally (Without Docker)

```python
# Start server in background, bind to random port
import subprocess, time
proc = subprocess.Popen([sys.executable, 'start_grpc_server.py', '--port', '0'],
                        stdout=subprocess.PIPE, cwd='apps/solver')
# Read port from stdout, then test with grpc.insecure_channel(f'localhost:{port}')
```

---

*Last updated: 2026-08-15 — after P0-P3 integration work, dual-path consolidation*
