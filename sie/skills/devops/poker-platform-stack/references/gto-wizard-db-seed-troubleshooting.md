# GTO Wizard Clone — Database Seeding & API Troubleshooting

## Database Setup

The GTO Wizard Clone uses SQLite (fallback when PostgreSQL unavailable) at:

**Host path:** `/home/sean/gto-wizard-clone/gto_wizard.db`
**Container path:** `/workspace/gto-wizard-clone/gto_wizard.db`

### Common Issues

#### 1. Seed Scripts Fail With ImportError
```
from apps.api.services.database import engine, Base
ImportError: cannot import name 'engine'
```

**Root cause:** The seed scripts (`apps/api/prisma/seed.py`, `apps/api/prisma/seed_course_data.py`) import `engine` as a global from `database.py`, but the async refactor replaced it with `get_engine()` function — no global `engine` is exposed.

**Fix:** Rewrite seed scripts to use `get_engine()`:
```python
from apps.api.services.database import get_engine, Base
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

async def seed():
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # ... insert data
```
Or use a standalone script that creates its own engine:
```python
from sqlalchemy.ext.asyncio import create_async_engine
from apps.api.services.database import Base
engine = create_async_engine("sqlite+aiosqlite:///gto_wizard.db")
async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
```

#### 2. aiosqlite Module Not Found
```
ModuleNotFoundError: No module named 'aiosqlite'
```

**Root cause:** aiosqlite is installed in a different venv (or not installed). The API runs from `/home/sean/hermes-apps-venv/`.

**Fix:**
```bash
/home/sean/hermes-apps-venv/bin/pip install aiosqlite --quiet
```

#### 3. Index Already Exists Error on Second Run
```
sqlite3.OperationalError: index ix_quiz_spots_street already exists
```

**Root cause:** Using `Base.metadata.create_all` with `checkfirst=True` (the default), but SQLAlchemy's index creation sometimes fails on SQLite when the index already exists from a previous schema version.

**Fix:** Drop and recreate the DB, or handle the error gracefully:
```python
async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
```
Simply truncate and re-run — the create_all checks for table existence but not index existence on some SQLAlchemy+aiosqlite versions.

### API Endpoints Map (notable routes)

| Frontend Route | API Route | Notes |
|---|---|---|
| `/strategies` | `/api/v1/strategy` (singular) | Nav link may point to wrong route |
| `/equity` | `/api/v1/equity/calculate` | GET (query) and POST (JSON body) |
| — | `/api/v1/strategy-lookup` | Strategy lookup by board/stack/position |
| — | `/api/v1/trainer/question` | Training mode question |
| — | `/api/v1/trainer/submit` | Training mode submission |

### Seed Data Files
- `apps/api/prisma/seed.py` — 50+ NLH quiz spots
- `apps/api/prisma/seed_course_data.py` — 3 training courses with lessons

Both need the `engine`→`get_engine()` import fix before they can run.

### Deployment Architecture
- **Frontend:** Host `next-server` on port 8564 (auto-managed by host process manager)
- **API:** Host `uvicorn` on port 8003 (runs from `hermes-apps-venv`)
- **Tunnel:** Cloudflare (`wiz.codeovertcp.com` → host localhost:8564)
- **Container:** Has a synced copy at `/workspace/gto-wizard-clone/`
- **SSH from container to host:** `ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1`
- **Host process management:** `next-server` auto-restarts when killed — update host tunnel config or deploy to same port
