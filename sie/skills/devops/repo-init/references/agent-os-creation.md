# agent-os Creation — 2026-05-01 Late Session Transcript

## What Was Built

`ChonSong/agent-os` — fresh start, zero git history in migrated packages.

## Exact Commands

### Create GitHub repo
```python
req = urllib.request.Request(
    "https://api.github.com/user/repos",
    data=json.dumps({"name": "agent-os", "description": "Autonomous agent operating system..."}).encode(),
    headers={"Authorization": f"token {GH_TOKEN}"},
    method="POST"
)
```

### Clone + first commit
```bash
git clone https://github.com/ChonSong/agent-os.git /opt/data/agent-os
cd /opt/data/agent-os
git config user.email "seanos1a@gmail.com"
git config user.name "Sean"
```

## Decisions Made

| Decision | Choice |
|----------|--------|
| Monorepo tools | turbo + nx dual config |
| Node version | 20 |
| Python version | 3.11 |
| Go version | 1.23 |
| CI approach | Path-filtered per language (python/node/go jobs, `needs: [changes]` pattern) |
| Docker | Individual Dockerfiles per app |
| PostgreSQL | Neon (serverless), connection string via GitHub Actions secrets |
| TypeScript publishing | GitHub Packages, `release.yml` handles auth |
| Release | Semantic release on main merge |
| Python packages | Editable install (`pip install -e .`) in CI |

## File Structure Created

```
agent-os/
├── apps/dashboard/
│   ├── frontend/         # Vite + React + TypeScript
│   │   ├── package.json  # name: @chonsong/dashboard-frontend
│   │   ├── vite.config.ts
│   │   └── src/
│   │       ├── main.tsx
│   │       └── App.tsx
│   └── backend/          # Express + Socket.io
│       ├── package.json  # name: @chonsong/dashboard-backend
│       └── src/
│           └── index.ts  # health endpoint works
├── packages/
│   ├── nanobot/          # pyproject.toml stub (source from ChonSong/nanobot fork)
│   ├── observability/    # ✅ AIEEvent + JSONL logger + drift scoring + tests
│   ├── agent-adapter/    # ✅ AgentAdapter ABC + NanobotAdapter + tests
│   └── shared-types/     # ✅ TypeScript types (AIEEvent, AgentResponse, Document)
├── infra/CasaOS/
│   ├── agent/            # go.mod stub
│   └── webhook-emitter/  # go.mod stub
├── .github/workflows/
│   ├── ci.yml            # ✅ Path-filtered python/node/go jobs, `|| true` guards
│   ├── release.yml       # ✅ Semantic release
│   └── deploy.yml        # Skeleton
├── turbo.json            # ✅ Turborepo config
├── nx.json                # ✅ Nx + @nx-go plugin
├── pyproject.toml         # ✅ Python workspace root
├── go.mod                 # ✅ Go module root
└── SPEC.md                # ✅ Architecture + PostgreSQL schema
```

## CI Result

First commit `e74018d` showed yellow (pending) then green on GitHub Actions.

## Roadmap Tasks Queued

| # | Task | Status |
|---|------|--------|
| 6 | Fork HKUDS/nanobot → ChonSong/nanobot | pending |
| 7 | Migrate nanobot → packages/nanobot/ | pending |
| 8 | Migrate Go packages → infra/CasaOS/ | pending |
| 9 | Extract claw-aie → packages/observability/ | pending |
| 10 | Wire agent-adapter into dashboard backend | pending |
| 11 | Publish shared-types to GitHub Packages | pending |
| 12 | PostgreSQL schema + Alembic migrations | pending |
| 13 | Terraform skeleton (Neon + Cloudflare) | pending |
| 14 | skills/tunnel-manager/SKILL.md | pending |

## Key Lesson

**Do NOT bring git history when migrating packages.** HKUDS/nanobot history stays at HKUDS/nanobot. `ChonSong/nanobot` is a fresh fork that can sync from upstream but doesn't carry history into `agent-os/packages/nanobot/`. The `hermes-sync` repo carries the roadmap and learning, not the source history.
