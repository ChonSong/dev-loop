# 2026-06-11 — GTO Wizard Recovery from Scratch

## Context
The `~/gto-wizard-clone/` repo directory was deleted from the filesystem. All GTO Wizard services were down (API on 8003, frontend on 8564, Cloudflare tunnel). No database backup existed.

## Recovery Sequence

### Step 1: Find the code

The repo at `~/gto-wizard-clone/` didn't exist. GitHub `ChonSong/gto-wizard-clone` returned HTTP 200 — the remote was alive. Cloned to `/workspace/gto-wizard-clone/`.

### Step 2: Install Python dependencies

```bash
cd /workspace/gto-wizard-clone

# Core game logic package (local editable install)
pip install -e ./packages/poker-core

# Missing production dependencies (not in pyproject.toml)
pip install phevaluator
pip install fakeredis
pip install sqlalchemy[asyncio]
pip install aiosqlite
pip install python-jose[cryptography]
pip install passlib[bcrypt]
pip install python-socketio
```

**Package issues encountered:**
- `gto_poker` editable install: `.pth` file referenced deleted path `/home/hermeswebui/gto-wizard-clone/packages/poker-core/src` — had to reinstall
- `phevaluator` was missing despite being required by `gto_poker` at runtime
- `fakeredis` needed for dev/test fallback when Redis isn't running

### Step 3: Start API backend

```bash
export PATH="/home/hermeswebui/.hermes/node/bin:$PATH"
cd /workspace/gto-wizard-clone
PYTHONPATH="apps/api:packages/poker-core/src" \
  uvicorn apps.api.main:app --host 0.0.0.0 --port 8003 --log-level warning &
```

API root at `/` returned `{"message":"GTO Wizard Clone API","version":"0.1.0","status":"running"}`.
Health endpoint at `/api/v1/health` returned `{"status":"healthy"}`.
Swagger UI at `/docs`.

### Step 4: Install and build frontend

```bash
cd /workspace/gto-wizard-clone/apps/web
npm install   # 511 packages, monorepo with npm workspaces
NEXT_PUBLIC_API_URL=http://localhost:8003 npx next build   # 20 static pages
NEXT_PUBLIC_API_URL=http://localhost:8003 npx next start -p 8564 &
```

**Issues:**
- Node was at `/home/hermeswebui/.hermes/node/bin/node` — not in PATH. `npm install` failed with `env: 'node': No such file or directory`. Fixed by `export PATH="/home/hermeswebui/.hermes/node/bin:$PATH"`.
- Build produced 20 static pages.

### Step 5: Verify

```bash
curl http://localhost:8003/        # 200 — API root
curl http://localhost:8003/docs    # 200 — Swagger UI
curl http://localhost:8564/        # 200 — Frontend HTML
curl http://localhost:8564/api/v1/health  # 200 — proxied to API
```

### What was lost

- SQLite database `gto_wizard.db` — auto-recreated on first API start
- All seed data (quiz spots, courses, strategies) — `Base.metadata.create_all()` runs on startup but no seed scripts exist, so the database starts empty

### What survived

- All source code on GitHub (`ChonSong/gto-wizard-clone`)
- Hermes skills and reference docs (24 files at `~/.hermes/skills/devops/gto-wizard-deployment/`)
- Cloudflare tunnel config (separate config file at `~/.cloudflared/`)

### Keys to a fast recovery

1. **GitHub backup worked** — without it, recovery would need source reconstruction from skills and reference docs
2. **Python dependency list was discoverable** — `gto_poker/setup.py` listed core deps; runtime errors revealed missing ones
3. **No seed script needed** — SQLAlchemy auto-creates tables on first API startup; trade-off is empty database after recovery
