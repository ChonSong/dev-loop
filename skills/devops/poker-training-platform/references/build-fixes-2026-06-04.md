# GTO Wizard Clone — Build Fixes (2026-06-04)

## API Test Fixes

### Problem: 9 test imports failing
**Symptoms:** `ModuleNotFoundError: No module named 'apps'` when running `pytest apps/api/tests/`
**Root cause:** Tests importing from `apps.api.routers` → routers import `apps.api.models` → models import `Base` from `apps.api.services.database`, which didn't export `Base` (only `DeclarativeBase` was defined).

**Fix sequence:**
1. Added `class Base(DeclarativeBase): pass` to `database.py`
2. Added `get_db_session()` async generator for FastAPI dependency injection
3. Fixed `quiz.py` import: `from apps.api.services.database import get_session_factory as async_session_factory`
4. Fixed `strategy_storage.py`: added `timezone` import (`from datetime import datetime, timezone`)
5. Fixed test data: `strategy_data` changed from `List[Dict]` to `Dict[str, Any]`
6. Made `store_strategy` and `get_strategy` tests async (`@pytest.mark.asyncio`)
7. All 9 tests passing

### Key import chain pattern
When `pytest apps/api/tests/` fails with ModuleNotFoundError:
```
test_solver_api.py
  → apps.api.routers.__init__ (imports ALL routers)
    → apps.api.routers.quiz.py
      → apps.api.services.database → needs get_db_session
      → apps.api.services.quiz_models → needs Base
    → apps.api.routers.hh.py
      → apps.api.services.database → needs Base, get_db_session
      → apps.api.models.hh_models → needs Base
```
**Lesson:** When a router imports from models/services, the entire chain must be importable. Missing `Base` in `database.py` cascades to all routers.

## Pydantic v2 Deprecation Warnings

Three files triggered PydanticDeprecation warnings:
1. `HandHistoryResponse` — `class Config: from_attributes = True`
2. `HandTagResponse` — same pattern
3. `BatchImportRequest` — `Field(..., max_items=N)` deprecated

Fixed by replacing with `model_config = {"from_attributes": True}` and `max_length=N`.

## Protobuf Version Fix

Error: `gencode 6.31.1 runtime 5.29.6`
Fix: `pip install "protobuf~=5.29"`
Check: `python3 -c "import google.protobuf; print(google.protobuf.__version__)"`

## Frontend package.json Merge

Remote had diverged `apps/web/package.json` (dependabot/turbo update). Fix:
```bash
git pull --rebase origin main
# Conflicts in: package.json, package-lock.json, sw.js
git checkout --theirs apps/web/package.json apps/web/public/sw.js package-lock.json
git add -A
GIT_EDITOR=true git rebase --continue
git push origin main
```
