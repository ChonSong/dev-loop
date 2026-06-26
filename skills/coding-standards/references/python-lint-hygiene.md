# Python Lint Sweep — F401/F403/F841 Fix Workflow

Systematic procedure for reducing Python lint noise on a ruff-checked project.

## 1. Assess scope

```bash
ruff check . --statistics
```

Reads the error count per category. Target: zero F401 (unused import), F403 (star import), F841 (unused variable). E402/E701/E741 are usually style-only and may be intentional.

## 2. Auto-fix pass

```bash
ruff check . --fix --unsafe-fixes
```

Handles what ruff can auto-fix: F841, E712 (True/False comparisons), some F401.

## 3. Manual F401/F403 suppression patterns

### 3a. Re‑export pattern (routers/`__init__.py`)

When a blanket `from . import X, Y` triggers F401 but the imports are intentional re-exports:

```python
# BEFORE (triggers F401)
from . import equity, solver, auth, hh

# AFTER (explicit re-export silences F401)
from . import equity as equity
from . import solver as solver
from . import auth as auth
from . import hh as hh
```

The `as X` suffix signals to ruff that the import is intentional.

### 3b. Try/except availability check

When the import exists only to test whether a module is available (skip test, degrade gracefully):

```python
# BEFORE (triggers F401)
try:
    from gto_poker.icm import icm_for_push_fold, get_standard_prizes
except ImportError:
    pytest.skip("icm_for_push_fold not available")

# AFTER — import the module, add noqa
try:
    import gto_poker.icm  # noqa: F401 — availability check
except ImportError:
    pytest.skip("gto_poker.icm not available")
```

Same pattern works for health‑check endpoints that just verify a module loads:

```python
try:
    import cfr.engine  # noqa: F401 — availability check
    return {"status": "ok", "engine": "MCCFR", ...}
except ImportError as e:
    return {"status": "degraded", "detail": str(e)}
```

### 3c. Wildcard import (verify‑only scripts)

When `from x import *` is intentional (e.g. a quick‑verify script):

```python
from gto_poker import *  # noqa: F403
```

### 3d. Dead imports — truly unused

When ruff flags an import that is genuinely not used:

```python
# Remove the unused symbol from the import line
from games.texas_hold_em import TexasHoldEm, create_river_state  # removed ActionType
```

## 4. Verify

```bash
# Remaining lint: should be only style issues (E402, E701, E741)
ruff check . --statistics

# Test the affected modules
pytest packages/poker-core/tests/ -x -q
pytest apps/solver/tests/test_solver_pipeline.py -x -q
```

## 5. Commit

```bash
git add -A && git commit -m "auto: <repo> T2 — fix F401/F403 lint warnings"
```

## When to skip

- If the remaining F401/F403 count is single‑digit and all are in intentional import blocks (availability checks, `__init__.py` re‑exports), consider them closed — no need to chase every last one.
- E402/E701/E741 style issues are low‑value to fix; only pursue if a user specifically requests clean `ruff check .` output.
