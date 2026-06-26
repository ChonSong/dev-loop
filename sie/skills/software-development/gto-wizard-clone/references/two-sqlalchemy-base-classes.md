# Two SQLAlchemy Base Classes Problem

## The Issue

The GTO Wizard Clone backend has TWO SQLAlchemy `Base` classes:

1. **`apps/api/services/database.Base`** — async `DeclarativeBase` via `sqlalchemy.orm.DeclarativeBase`. Used by hh_models and quiz_models. Created by `init_db()`.

2. **`apps/api/services/models.Base`** — sync `declarative_base(cls=AsyncAttrs)` via `sqlalchemy.orm.declarative_base`. Used by Course, CommunitySpot models. **NOT** created by `init_db()`.

## The Consequence

`init_db()` in `database.py` calls `Base.metadata.create_all()` on `database.Base`. Tables registered on `models.Base` (courses, community_spots, lessons, etc.) are **never auto-created**. They must be created manually or the `init_db()` function must know about both bases.

## Detection

Backend returns 500 with: `sqlite3.OperationalError: no such table: courses` even though the log says "Database tables initialized."

## Fix Options

### Option A: Create manually (used in this project)

```python
import sqlite3
conn = sqlite3.connect('/workspace/gto_wizard.db')
c = conn.cursor()
c.execute('''CREATE TABLE courses (...)''')
conn.commit()
```

### Option B: Register all models on the same Base

Move Course, CommunitySpot, etc. from `services.models.Base` to `database.Base`. Requires changing imports in 4+ model files.

### Option C: Create from metadata

```python
from apps.api.services.models import Base as SyncBase
async with engine.begin() as conn:
    await conn.run_sync(SyncBase.metadata.create_all)
```

## Prevention

When adding new SQLAlchemy models, always check which `Base` they inherit from. If they use a different `Base` than the one used by `init_db()`, the tables won't be created automatically.
