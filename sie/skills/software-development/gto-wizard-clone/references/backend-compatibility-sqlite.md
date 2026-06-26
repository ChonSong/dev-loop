# Backend SQLite Compatibility Fixes

The GTO Wizard Clone backend uses SQLAlchemy with async SQLite (aiosqlite).
Several PostgreSQL-specific types required migration:

## 1. JSONB -> sqlalchemy.JSON

PostgreSQL JSONB crashes SQLite compiler. Replace everywhere:
- `from sqlalchemy.dialects.postgresql import JSONB` → `from sqlalchemy import JSON`
- `Column(JSONB, ...)` → `Column(JSON, ...)`

Find: `grep -rn "JSONB" apps/api/ --include="*.py" | grep -v database.py`

## 2. PostgreSQL UUID -> String(36)

`UUID(as_uuid=True)` crashes SQLite. Replace:
- `Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)` → `Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))`

## 3. ARRAY -> JSON

`ARRAY(Numeric(...))` crashes SQLite. Replace with `mapped_column(JSON, nullable=True, default=list)`.

Affects: `quiz_models.py` (accuracy_history, missed_spot_ids), `spots.py` (tags)

## 4. Quiz Router Session Context Bug

`get_session_factory` returns `async_sessionmaker` — does NOT support async context manager.
Fix: use `get_session_context()` (async context manager) instead.

```python
from apps.api.services.database import get_session_context
async with get_session_context() as session:
    await session.execute(...)
```

## 5. Database File Location

Resolves from `services/database.py` up 4 levels → `/workspace/gto_wizard.db`, NOT repo root.

## 6. Dual Base Classes

Two different Base classes exist: `database.Base` (async, auto-created by init_db()) and `services.models.Base` (sync, NOT auto-created). Tables on the wrong Base must be created manually or refactored to the async Base.
