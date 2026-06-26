# Hermes-Sync Repo Structure (Verified 2026-05-19)

## What's actually in the git repo

```
hermes-sync/
├── config.yaml        ← config IS at ROOT (not in config/ subdir!)
├── SOUL.md
├── auth.json
├── secrets.age
├── secrets/.env       ← git-tracked, NOT gitignored
├── memory/            ← separate from memories/
├── memories/          ← merge both into ~/.hermes/
├── skills/
├── workspace/
├── sessions/          ← JSON session transcripts
├── cron/jobs.json
├── docker/
├── scripts/
├── references/
└── projects/
```

## Critical path differences from assumptions

| Expected path | Actual path | Notes |
|---------------|-------------|-------|
| `config/config.yaml` | `config.yaml` (root) | Common pattern: config dir vs config file |
| `memory/` only | `memory/` AND `memories/` | Both exist; merge both |
| `secrets/` gitignored | `secrets/.env` git-tracked | `.env` in secrets/ is versioned |

## Bootstrap rsync commands (corrected)

```bash
# config.yaml (file, not directory)
cp "${HERMES_SYNC_DIR}/config.yaml" "${HERMES_DIR}/config.yaml"

# skills (full recursive)
rsync -av --delete "${HERMES_SYNC_DIR}/skills/" "${HERMES_DIR}/skills/"

# memory + memories (BOTH, merge into ~/.hermes/memories/)
rsync -av "${HERMES_SYNC_DIR}/memory/" "${HERMES_DIR}/memories/"
rsync -av "${HERMES_SYNC_DIR}/memories/" "${HERMES_DIR}/memories/"

# SOUL.md
rsync -av "${HERMES_SYNC_DIR}/SOUL.md" "${HERMES_DIR}/"

# workspace
rsync -av --delete "${HERMES_SYNC_DIR}/workspace/" "${WORKSPACE_DIR}/"
```

## If adding new files to hermes-sync

- **Config files**: commit at repo root (`config.yaml`), NOT in a `config/` subdirectory (that dir doesn't exist in git)
- **Secrets**: `secrets/.env` is git-tracked; `secrets.age` is gitignored
- **Memory files**: go to `memory/` (for MEMORY.md/USER.md) — `memories/` is also available if you want separation