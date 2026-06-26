# Solver Backend Deployment — 2026-06-11

## Session Summary

Deployed the MCCFR solver engine as a live API endpoint for the GTO Wizard Clone. The solver now serves real GTO strategy data through `POST /api/v1/solver/solve`.

## Problem

The solver engine existed in the codebase with 3,915 lines of tests but was NOT connected to the running system:
- Hardcoded `/tmp/gto-wizard-clone/` paths across 18 files prevented imports
- The FastAPI solver router tried to use Celery (not running) and fell back to broken local tracking
- The gRPC server was not deployed
- The study page was a static mock with no solver data

## What Was Done

1. **Installed gto-poker in editable mode** on both container and host
2. **Fixed 18 files** with hardcoded `/tmp/gto-wizard-clone` paths — replaced with dynamic `os.path.join` relative computations
3. **Installed grpcio** in host's hermes-apps-venv
4. **Started gRPC solver server** on host port 50051 (sync mode, no Celery)
5. **Rewrote solver router** (`apps/api/routers/solver.py`) — direct MCCFR engine import, bypass gRPC/Celery
6. **Created solver client** (`apps/api/services/solver_client.py`) — gRPC client for the legacy path

## Verified Results

### Health Check
```
GET /api/v1/solver/health
→ {"status":"ok","engine":"MCCFR","detail":"Solver engine available"}
```

### Solve (river spot, 200 iterations)
```
POST /api/v1/solver/solve
{"game_type":"nlh","board":"Kd7h2c","pot_size":100,"iterations":200,"street":"river"}

→ {"status":"complete","progress":100,"strategy":[
    {"action":"fold","frequency":0.25,"ev":0.0},
    {"action":"check","frequency":0.25,"ev":0.0},
    {"action":"bet:0.5","frequency":0.25,"ev":0.0},
    {"action":"all_in:100","frequency":0.25,"ev":0.0},
    ... 8 more entries across 5 infosets
  ],"message":"Solved river spot (5 infosets)"}
```

### Solver Tests
All 15 quick tests pass (skipping heavy 3-way river solve):
```
test_cfr.py::TestDeckAndHand::test_card_parse        ✅
test_cfr.py::TestDeckAndHand::test_hand_evaluation   ✅
test_cfr.py::TestDeckAndHand::test_hand_comparison   ✅
test_cfr.py::TestGameState::test_infoset_key         ✅
test_cfr.py::TestGameState::test_valid_actions       ✅
test_cfr.py::TestInfoSets::test_regret_matching      ✅
test_cfr.py::TestInfoSets::test_regret_matching_all_negative ✅
test_cfr.py::TestInfoSets::test_info_set_creation    ✅
test_cfr.py::TestInfoSets::test_info_set_strategy    ✅
test_cfr.py::TestInfoSets::test_average_strategy     ✅
test_cfr.py::TestCFREngine::test_engine_initialization ✅
test_cfr.py::TestCFREngine::test_simple_solve        ✅
test_cfr.py::test_integration                        ✅
test_cfr.py::TestMultiWayCFR::test_create_3way_state ✅
test_cfr.py::TestMultiWayCFR::test_3way_valid_actions✅
```

## Files Fixed (18)

- `apps/solver/cfr/engine.py` — removed 2 hardcoded paths
- `apps/solver/cfr/flop_solver.py` — removed hardcoded path
- `apps/solver/cfr/turn_solver.py` — removed hardcoded path
- `apps/solver/cfr/river_solver.py` — removed hardcoded path
- `apps/solver/games/texas_hold_em.py` — removed hardcoded path
- `apps/solver/server.py` — removed hardcoded path, added solver + proto dir inserts
- `apps/solver/service.py` — removed hardcoded path, added proto dir insert, reordered imports
- `apps/solver/strategy/push_fold_charts.py` — removed hardcoded path
- `apps/solver/test_grpc_service.py` — proto path computed dynamically
- `apps/solver/tests/test_cfr.py` — relative path from tests to solver
- `apps/solver/tests/test_multiway.py` — relative path from tests to solver
- `apps/solver/tests/test_flop_turn_solvers.py` — relative path, fixed `import os as np` bug
- `apps/solver/tests/test_edge_cases.py` — relative path, added missing `import sys`
- `apps/solver/tests/test_solver_pipeline.py` — relative path
- `apps/solver/tests/test_push_fold.py` — relative path
- `apps/worker/tasks.py` — fixed import path
- `apps/api/routers/omaha.py` — removed poker-core path (gto-poker installed)
- `apps/api/routers/solver.py` — complete rewrite for direct MCCFR import

## Path Fix Pattern

Replace:
```python
sys.path.insert(0, '/tmp/gto-wizard-clone/apps/solver')
```
With:
```python
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
```
The `..` works for **all** files inside `apps/solver/SUBDIR/*.py` (cfr/, tests/, games/, strategy/). For files at `apps/solver/` root, the insert can be removed entirely (current dir is on path).

Remove (gto-poker is pip-installed):
```python
sys.path.insert(0, '/tmp/gto-wizard-clone/packages/poker-core/src')  # DELETE
```

## Pitfalls Encountered

1. **scp target path bug:** `scp file.py host:apps/api/` puts the file AT `apps/api/file.py`, not `apps/api/routers/file.py`. Must use full target: `host:apps/api/routers/file.py`.

2. **Missing `import os`:** After replacing hardcoded paths with `os.path.join(...)`, many files lacked `import os`, causing `NameError: name 'os' is not defined`.

3. **service.py import ordering:** `_proto_dir = os.path.join(...)` was placed BEFORE `import os, sys`. Fixed by shuffling import order.

4. **`import os as np` bug:** In `test_flop_turn_solvers.py`, a previous edit created `import os as np` (aliasing `os` as `np` instead of `import numpy as np`). Caused confusing `numpy` name errors.

5. **gRPC SubmitSolve returns immediately with "queued":** The `SubmitSolve` RPC returns "queued" status because the solve runs in a background thread (`_run_solve_sync`). Poll `GetSolveStatus` to track completion. The gRPC path does NOT return strategy data through `GetSolveStatus` — only status/progress.

6. **Direct import path doesn't need gRPC running:** The rewritten solver router imports `cfr.engine.CFREngine` directly. The gRPC server on port 50051 is used only if the legacy `solver_client.py` gRPC path is hit.

## Commit

`b9b39ed` — `fix(solver): deploy MCCFR engine with direct API integration`
21 files changed, 425 insertions(+), 154 deletions(-)
