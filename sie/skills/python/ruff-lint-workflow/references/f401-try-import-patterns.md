# F401 in Try/Except ImportError Blocks

## Problem

Ruff flags F401 when names are imported inside a `try/except ImportError` block but never referenced after the import. This commonly happens when:

1. **Availability-check imports**: The `try` block exists solely to detect whether a module/name is available. The imported names are never used — only the success/failure of the import matters.
2. **Partial usage**: Some names from the import are used, but others aren't.

## Pattern 1: Availability-Check → `importlib.util.find_spec`

Replace the try/except with a direct spec check:

```python
# Bad — F401 on `icm_for_push_fold`, `get_standard_prizes`
try:
    from gto_poker.icm import icm_for_push_fold, get_standard_prizes
except ImportError:
    pytest.skip("icm_for_push_fold not available")

# Good — no unnecessary imports
import importlib

if importlib.util.find_spec("gto_poker.icm") is None:
    pytest.skip("icm_for_push_fold not available")
```

**Advantages**: Zero unused imports, no suppression needed, intent is clearer (we're checking package availability, not importing for use).

**Requires**: `import importlib` at module level (safe — stdlib, always available).

## Pattern 2: Remove Truly Unused Names from an Otherwise-Needed Import

When a `try` block imports multiple names but only some are used:

```python
# Bad — ActionType and Deck are unused
try:
    from cfr.engine import CFREngine
    from games.texas_hold_em import TexasHoldEm, create_river_state, ActionType
    from gto_poker.deck import Deck
    from gto_poker.hand import HandEvaluator
except ImportError:
    raise HTTPException(503, "solver engine not available")

# Good — only what's used
try:
    from cfr.engine import CFREngine
    from games.texas_hold_em import TexasHoldEm, create_river_state
    from gto_poker.hand import HandEvaluator
except ImportError:
    raise HTTPException(503, "solver engine not available")
```

## Pattern 3: Health-Check Endpoints

For health/status endpoints that check engine availability, use `find_spec` inline:

```python
try:
    import importlib.util
    if importlib.util.find_spec("cfr.engine") is None:
        raise ImportError("cfr.engine not available")
    return {"status": "ok", "engine": "MCCFR"}
except ImportError as e:
    return {"status": "degraded", "detail": str(e)}
```

This avoids importing a name just to check it exists.

## When NOT to Refactor

- If the imported name IS actually used later in the function (e.g., `CFREngine(game=game)`), **keep the import**. Ruff won't flag it.
- If the module has side effects that must run at import time, keep the `try/except` with `# noqa: F401`.
- For test fixtures where the import guards a real test of the import path itself, keep the original pattern.
