# Database Seeding — GTO Wizard Clone

## Overview

The GTO Wizard Clone uses SQLite (via `aiosqlite`) as the local dev database, with SQLAlchemy async ORM. A unified seeder script exists at `/workspace/gto-wizard-clone/seed_all.py`.

## Dual Base Problem

The project has **two separate `declarative_base()` instances**:

```python
# Base 1 — used by quiz_models.py, hh_models.py
from apps.api.services.database import Base as MainBase

# Base 2 — used by course_models.py, spots.py
from apps.api.services.models import Base as StrategyBase
```

`MainBase.metadata.create_all()` only creates tables for models registered with `MainBase`. Both must be created.

## DB Path

```python
# In database.py — resolves to /workspace/gto_wizard.db
_sqlite_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "gto_wizard.db")
DATABASE_URL = f"sqlite+aiosqlite:///{os.path.abspath(_sqlite_path)}"
```

## Running the Seeder

```bash
cd /workspace/gto-wizard-clone && python3 seed_all.py
```

Seeds:
1. **Quiz spots** (60 spots across 25+ categories × 3 difficulties)
2. **Training courses** (3 courses × 8 lessons = 24 lessons)
3. **Push/fold strategy data** (18 entries: Nash charts for 5 positions × 5 stack depths + 3 ICM bubble ranges)

Idempotent — checks existing counts and skips if already populated.

## Known Pitfalls

### 1. `index=True` + explicit `Index()` on same column
SQLAlchemy creates the auto-named index from `index=True`, then the explicit `Index()` tries to create again → `OperationalError: index already exists`. Fix: remove `index=True` if an explicit `Index()` is defined.

**Fixed in `quiz_models.py`:** `street` column had both `index=True` and `Index("ix_quiz_spots_street", "street")`.

### 2. `drop_all` doesn't drop indexes in SQLite
After `drop_all`, orphan indexes may persist. Solution: delete the `.db` file entirely, or use `checkfirst=True` on `create_all`.

### 3. Engine singleton caching
`database.py` caches `_engine` globally. If you delete the `.db` file, reset:
```python
import apps.api.services.database as db_mod
db_mod._engine = None
db_mod._session_factory = None
```

### 4. `video_url` column in Lesson table
The `Lesson` model has `video_url = Column(Text, nullable=True)`. When inserting, either include `video_url=None` explicitly or ensure the column is nullable.

### 5. `strategy_data` JSON column
Pass a dict when inserting (SQLAlchemy handles serialization). Querying returns a dict (or string if using raw SQL — use `json.loads()`).

## Schema Changes

When adding new models or columns:
1. Update the model file
2. Delete the old `.db` file (SQLite has limited `ALTER TABLE` support)
3. Re-run `seed_all.py` to recreate and re-seed
