---
name: repo-init
description: "Initialize a new project repository from scratch: monorepo scaffolding (turbo + nx), Docker setup, CI/CD pipeline (GitHub Actions + path filtering + semantic release), PostgreSQL (Neon), and secrets management. Used when creating net-new projects under ChonSong."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [repo-creation, monorepo, docker, github-actions, terraform, neon]
    track: infrastructure
    project: agent-os
---

# repo-init — New Project Repository Initialization

Create a production-ready open-source repository from scratch. Applies to ChonSong net-new projects. For existing repo migrations, see `repo-discovery` + `github-repo-management`.

## Trigger Conditions

- User asks to create a new repo (e.g., "create a new project called X")
- Roadmap task type is `setup` for a new repo
- A project migrates from a scaffold to a production-ready monorepo

## ⚠️ Critical: GitHub Token Discovery

**The GitHub token is NOT hardcoded anywhere. Always discover it at runtime.**

Token source priority:
1. **`~/.hermes/.env`** → `GITHUB_TOKEN=ghp_...` (primary — this is where Hermes stores it)
2. `~/.git-credentials` → only works if `credential.helper=store` is set, format: `https://user:TOKEN@github.com`
3. Environment `GITHUB_TOKEN` env var

**To read from `.env`:**
```python
import os, pathlib
hermes_home = os.environ.get('HERMES_HOME', '/home/hermeswebui/.hermes')
token = ''
with open(pathlib.Path(hermes_home) / '.env') as f:
    for line in f:
        if line.startswith('GITHUB_TOKEN='):
            token = line.split('=', 1)[1].strip()
            break
```

**Never hardcode a GitHub token in a skill.** Copy the token value at runtime from the discovered source.

## Architecture Decisions (Established 2026-05-01)

These are not arbitrary — they reflect hard lessons from `agent-os` and previous projects:

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Repo name | Descriptive, not clever | `agent-os` beats `claw-v2` |
| Monorepo tool | Turbo + Nx dual config | Turbo for task scheduling, Nx for Go/WSL support |
| Docker strategy | Individual Dockerfiles per app | `dashboard-frontend`, `dashboard-backend`, `agent-core` |
| CI trigger | Path-filtered per project | Avoids running Python tests on Go-only changes |
| Release | Semantic release + conventional commits | `feat:`, `fix:`, `chore:` prefix required |
| PostgreSQL | Neon (serverless) | Free tier, no self-hosting, connection string in secrets |
| Secrets | GitHub Actions secrets + `.env.example` | Never commit secrets, always provide `.env.example` |
| Git history | Fresh start | Do NOT bring git history into migrated packages |

## Step-by-Step

### Step 1: Create GitHub Repo

```python
import urllib.request, json, os, pathlib

# Discover GitHub token at runtime — NOT hardcoded
hermes_home = os.environ.get('HERMES_HOME', '/home/hermeswebui/.hermes')
token = ''
with open(pathlib.Path(hermes_home) / '.env') as f:
    for line in f:
        if line.startswith('GITHUB_TOKEN='):
            token = line.split('=', 1)[1].strip()
            break

if not token:
    raise RuntimeError("GITHUB_TOKEN not found in ~/.hermes/.env")

repo_name = "my-new-repo"
description = "Description of the project"

req = urllib.request.Request(
    "https://api.github.com/user/repos",
    data=json.dumps({"name": repo_name, "description": description, "private": False}).encode(),
    headers={"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json", "User-Agent": "Hermes-Agent"},
    method="POST"
)
try:
    with urllib.request.urlopen(req, timeout=15) as r:
        result = json.loads(r.read())
        print(result["html_url"])
except urllib.error.HTTPError as e:
    error_body = json.loads(e.read())
    print(f"HTTP {e.code}: {error_body.get('message', e)}")
```

### Step 2: Clone Empty Repo

```bash
git clone https://github.com/ChonSong/{repo_name}.git /opt/data/{repo_name}
cd /opt/data/{repo_name}
git config user.email "seanos1a@gmail.com"
git config user.name "Sean"
```

### Step 3: Scaffold Monorepo Structure

```
{repo_name}/
├── apps/
│   └── dashboard/
│       ├── frontend/        # Vite + React + TypeScript
│       └── backend/         # Express + Socket.io
├── packages/
│   └── shared-types/        # TypeScript types (published to GitHub Packages)
├── infra/
│   └── CasaOS/
│       ├── agent/
│       └── webhook-emitter/
├── .github/workflows/
│   ├── ci.yml               # Path-filtered: python/node/go jobs
│   ├── release.yml          # Semantic release on main merge
│   └── deploy.yml           # Docker build + push on release
├── turbo.json               # Turborepo config
├── nx.json                  # Nx + @nx-go plugin
├── pyproject.toml           # Python workspace root
├── go.mod                   # Go module root
└── SPEC.md                  # Architecture spec + schema
```

### Step 4: Add CI/CD

**`.github/workflows/ci.yml`** — path-filtered matrix:

```yaml
name: CI
on: [push, pull_request]
jobs:
  python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -e packages/observability/
      - run: python -m pytest packages/observability/tests/ -v
        continue-on-error: true  # remove when tests exist

  node:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm install
      - run: npm run build --workspace=apps/dashboard/frontend
        continue-on-error: true

  go:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: go build ./...
        working-directory: infra/CasaOS/agent
        continue-on-error: true  # remove when go files exist
```

**`.github/workflows/release.yml`** — semantic release:

```yaml
name: Release
on:
  push:
    branches: [main]
jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', registry-url: 'https://npm.pkg.github.com' }
        env: { NODE_AUTH_TOKEN: ${{ secrets.GITHUB_TOKEN }} }
      - run: npm install
      - run: npx semantic-release
        env: { GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }} }
```

### Step 5: Add Docker Support

**`apps/dashboard/frontend/Dockerfile`:**
```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
```

**`apps/dashboard/backend/Dockerfile`:**
```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --omit=dev
COPY . .
EXPOSE 3001
CMD ["node", "dist/index.js"]
```

### Step 6: Add PostgreSQL (Neon) Schema Reference

In `SPEC.md`:
```markdown
## Database

PostgreSQL via **Neon** (serverless, free tier).

### Schema

```sql
-- Sessions
CREATE TABLE sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT NOT NULL,
  started_at TIMESTAMPTZ DEFAULT NOW(),
  ended_at TIMESTAMPTZ,
  metadata JSONB DEFAULT '{}'
);

-- AIE Events (journal)
CREATE TABLE aie_events (
  id SERIAL PRIMARY KEY,
  session_id UUID REFERENCES sessions(id),
  type TEXT NOT NULL,  -- delegation | tool_call | assumption | drift | circuit_open | task_complete
  timestamp TIMESTAMPTZ DEFAULT NOW(),
  data JSONB NOT NULL
);

-- Drift log
CREATE TABLE drift_log (
  id SERIAL PRIMARY KEY,
  session_id UUID REFERENCES sessions(id),
  assumption TEXT NOT NULL,
  correction TEXT NOT NULL,
  corrected_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Connection:** `NEON_DATABASE_URL` stored as GitHub Actions secret, injected via `deploy.yml`.
```

### Step 7: Push Initial Commit

```bash
git add .
git commit -m "feat: initial scaffold"
git remote add origin https://github.com/ChonSong/{repo_name}.git
git push -u origin main
```

## Patterns That Work

- **`|| true` guards in CI** — allow empty packages to pass CI until real code lands; remove guards as tasks complete
- **Path filtering via `needs: [changes]`** — matrix job outputs which paths changed; downstream jobs skip if their path wasn't touched
- **Individual Dockerfiles per app** — avoids building entire monorepo for a single app change; tags as `dashboard-frontend`, `dashboard-backend`, `agent-core`
- **Python editable install in CI** — `pip install -e .` lets tests import the package without publishing
- **`SPEC.md` as living architecture doc** — written at repo creation, updated with each major feature
- **Explicit uv workspace member paths** — when `packages/` contains both Python packages (with `pyproject.toml`) and Node/TypeScript packages (with `package.json`, `tsconfig.json`), use explicit paths like `members = ["packages/backend-core"]`. The glob `members = ["packages/*"]` fails because uv checks every matched directory for `pyproject.toml` and errors on non-Python packages.

## Anti-Patterns to Avoid

- **Single monolith Dockerfile** — rebuilds everything on any change
- **Committing `node_modules/` or `__pycache__/`** — add to `.gitignore` at creation
- **Committing credentials, tunnel secrets, or deployment configs** — `*creds*.json`, `*tunnel*.yml`, `*-config.yml` and similar patterns must be in `.gitignore` before first commit. A single `git add -A` can sweep 290+ untracked files including cloudflare tunnel secrets and screenshot artifacts.
- **Stale `.gitignore` that doesn't cover build artifacts** — monitor `git status --short` after new tooling is added. Generated pages (`apps/*/src/app/*/page.tsx`), visual QA screenshots (`snapshots/`, `refs/`), and `dist/` directories accumulate silently.
- **Secrets in env vars committed to repo** — always use `.env.example` with placeholder values
- **Git history in migrated packages** — fresh start; history stays in the source repo (e.g., HKUDS/nanobot)
- **Path deps in `requirements.txt`** — use `git+https://github.com/ChonSong/...` or `pip install -e git+...` for Docker compatibility
- **Monorepo package version drift** — root `package.json` and workspace must have the SAME version of framework deps. Root Next.js 16 + workspace 15 causes Turbopack errors (`File not found: server-external-packages.jsonc`, `RouteHas` type conflicts). Align root to match workspace.
- **`packages/*` glob in uv workspace** — when `packages/` contains both Python and Node/TS packages, using `members = ["packages/*"]` in `[tool.uv.workspace]` fails because uv expects every matched directory to have `pyproject.toml` and errors on Node-only directories (package.json, tsconfig.json, no pyproject.toml). Use explicit paths like `members = ["packages/python-pkg"]` instead.

## Secrets Checklist (before first release)

- [ ] `NEON_DATABASE_URL` — Neon connection string
- [ ] `CLOUDFLARE_API_TOKEN` — if using Cloudflare tunnels
- [ ] `DOCKER_HUB_TOKEN` — if pushing to Docker Hub
- [ ] `GITHUB_TOKEN` — provided automatically, use for npm GitHub Packages auth

## References

See `references/agent-os-creation.md` — full agent-os repo creation transcript (2026-05-01): exact commands, decisions made, CI output, and task queue.
See `references/poker-platform-stack.md` — domain knowledge for building a poker/GTO training platform (GTO Wizard clone): feature areas, open-source library stack, CFR algorithm notes, HH format overview, and recommended tech stack for this specific domain.

## Poker/GTO Platform Patterns (Domain-Specific)

### GTO Wizard Clone — Lessons Learned (June 2026)

**Repo:** `ChonSong/gto-wizard-clone` — open-source GTO poker training platform.

**Key Architecture Decisions That Worked:**
- FastAPI + Python solver + Next.js frontend with monorepo (Turbo + Nx)
- gRPC for solver service isolation (CPU-intensive CFR separate from API)
- Redis pub/sub for solver progress streaming to frontend via WebSocket
- PostgreSQL with JSONB for strategy storage
- All 7 game variants (NLH, PLO4, PLO5, Omaha Hi/Lo, Shortdeck, Double Board PLO, Bomb Pot)

**Libraries That Actually Got Used (Not Just Researched):**
- `HenryRLee/PokerHandEvaluator` — PLO4/PLO5/Hi-Lo (the critical one, 501⭐)
- `zekyll/OMPEval` — NLH (224⭐)
- Custom MCCFR solver (no suitable open-source option existed)
- Custom Double Board PLO and Bomb Pot implementations (truly novel — no reference impl)

**PLO4/PLO5 Specifics:**
- PokerHandEvaluator C++ library with Python bindings — `pip install git+https://github.com/HenryRLee/PokerHandEvaluator`
- PLO4: 4 hole cards, evaluate best 2-of-4 + best 3-of-5 board
- PLO5: 5 hole cards, evaluate best 4-of-5 + best 1-of-5 board (uses same library)

**Common Gotchas:**
- Protobuf version mismatch between generated code and runtime — pin versions explicitly
- `get_session_factory` / `get_db_session` naming — FastAPI dependency injection needs `get_db_session`, not `get_session_factory`
- `timezone` import from `datetime` — `from datetime import datetime, timezone` (easy to miss)
- Playwright E2E in containers needs `PLAYWRIGHT_BROWSERS_PATH` override AND system libs (glib2)

**Testing Infrastructure:**
- 580+ unit tests across poker-core, solver, and API
- Playwright E2E tests need: `PLAYWRIGHT_BROWSERS_PATH=/tmp/pw-browsers npx playwright install chromium`
- CI E2E config: separate `playwright.ci.ts` with no `webServer` (server started externally)
- Cron jobs for nightly test suite, 6h build verify, weekly version check
