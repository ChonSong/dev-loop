# SQLAlchemy Dual-Base Table Creation Fix

## The Problem

A project has two different SQLAlchemy `Base` classes because different model files import from different modules:

```python
# apps/api/services/database.py
class Base(DeclarativeBase): pass

# apps/api/services/models.py
Base = declarative_base(cls=AsyncAttrs)
```

Models register themselves on whatever base they import:

```python
# apps/api/services/quiz_models.py
from apps.api.services.database import Base  # registers on DbBase

# apps/api/models/spots.py
from apps.api.services.models import Base    # registers on ModelsBase
```

When `init_db()` only calls `ModelsBase.metadata.create_all`, tables registered on `DbBase` are never created, causing "no such table" errors at runtime.

## Diagnosis

1. Check which tables exist:
   ```python
   import sqlite3
   conn = sqlite3.connect('gto_wizard.db')
   tables = [r[0] for r in conn.execute(
       "SELECT name FROM sqlite_master WHERE type='table'"
   ).fetchall()]
   ```

2. Find which base a missing table is registered on:
   ```python
   from apps.api.models.course_models import Course
   from apps.api.services.database import Base as DbBase
   print('courses' in DbBase.metadata.tables)  # False → it's on ModelsBase
   ```

3. The error tells you which table is missing:
   `OperationalError: no such table: courses`

## Fix

In `init_db()`, call `create_all` on both bases:

```python
async with engine.begin() as conn:
    await conn.run_sync(ModelsBase.metadata.create_all)
    from apps.api.services.database import Base as DbBase
    await conn.run_sync(DbBase.metadata.create_all)
```

## Prevention

Standardize on one `Base` class across the project. If that's not feasible (models are in different packages), always call `create_all` on every base that has registered tables, or iterate `Base.registry.metadata.tables` to find all unique tables.

## Quick SQL Fix (when you can't restart the API)

To create a missing table in SQLite without the ORM:

```python
conn.execute('''
    CREATE TABLE IF NOT EXISTS courses (
        id TEXT PRIMARY KEY, title TEXT NOT NULL,
        description TEXT, ...rest of columns...
    )
''')
```

Then copy the DB to the path the API reads from and restart.
