# Batch Fix for Hardcoded /tmp/gto-wizard-clone Paths

## Problem

18 Python files across `apps/solver/`, `apps/api/`, and `apps/worker/` contained hardcoded `sys.path.insert(0, '/tmp/gto-wizard-clone/...')` references. These paths only exist when the repo is cloned to `/tmp/`, which breaks after container restart or when running from a different directory.

## Files Affected

```
apps/solver/cfr/engine.py
apps/solver/cfr/flop_solver.py
apps/solver/cfr/turn_solver.py
apps/solver/cfr/river_solver.py
apps/solver/games/texas_hold_em.py
apps/solver/server.py
apps/solver/service.py
apps/solver/strategy/push_fold_charts.py
apps/solver/tests/test_cfr.py
apps/solver/tests/test_multiway.py
apps/solver/tests/test_flop_turn_solvers.py
apps/solver/tests/test_edge_cases.py
apps/solver/tests/test_solver_pipeline.py
apps/solver/tests/test_push_fold.py
apps/solver/test_grpc_service.py
apps/worker/tasks.py
apps/api/routers/omaha.py
start_server.py
```

## Replacement Pattern

Two types of hardcoded path:

1. **`sys.path.insert(0, '/tmp/gto-wizard-clone/packages/poker-core/src')`** — Remove entirely (the `gto-poker` package is pip-installed in editable mode)

2. **`sys.path.insert(0, '/tmp/gto-wizard-clone/apps/solver')`** — Replace with dynamic relative path:
   ```python
   sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
   ```
   Where `..` is relative from the file's subdirectory to `apps/solver/`.

3. **Other string references** (e.g. `PROTO_DIR = '/tmp/gto-wizard-clone/apps/solver/proto'`) — Replace with:
   ```python
   PROTO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'proto')
   ```

## Critical: `import os` Must Be Present

Before the `sys.path.insert` call, ensure `import os` is already imported. Add near the top of the file with other stdlib imports:
```python
import os
```

## Verification

```bash
grep -rn '/tmp/gto-wizard' --include='*.py' . | grep -v fix_paths.py | grep -v start_server.py
# Should return no results
```

## Proto Import Gotcha

Files that import `solver_pb2_grpc` or `solver_pb2` need the proto directory on sys.path:
```python
import sys, os
_proto_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'proto')
if _proto_dir not in sys.path:
    sys.path.insert(0, _proto_dir)
import solver_pb2_grpc
import solver_pb2
```
The proto dir path must be computed AFTER `import os`.
