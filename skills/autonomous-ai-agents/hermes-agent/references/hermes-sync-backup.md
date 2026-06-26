# Hermes-Sync Backup Reference

## Overview

Hermes state is backed up to GitHub (`ChonSong/hermes-sync`) via a cron-based Python script (`/opt/data/scripts/hermes-backup.py`). The script copies all state files to a git working directory (`/opt/data/cache/sync-work/hermes-sync`), commits, and pushes.

**Last confirmed sync:** `bda234f` — 2026-05-08T13:29:22+1000 (38 files)

## Cron-Based Backup Script

**Script:** `/opt/data/scripts/hermes-backup.py`
**Wrapper:** `/opt/data/scripts/hermes-backup.sh` (bash wrapper that calls the Python script)

**Usage (from cron or shell):**
```bash
# Correct: bash wrapper sources .env for GITHUB_TOKEN
bash /opt/data/scripts/hermes-backup.sh

# Or with explicit env sourcing (more reliable):
bash -c 'set -a; source /opt/data/.env; set +a; export HOME=/home/sean; export HERMES_HOME=/opt/data; /usr/bin/python3 /opt/data/scripts/hermes-backup.py'
```

**Flags:**
- Default: git sync only (fast, safe for every 6h cron)
- `--full-image`: includes Docker image backup (slow, daily only)

**⚠ Pitfalls:**
1. **Don't run with `python3` on the `.sh` wrapper** — it's a bash script, not Python. `python3 hermes-backup.sh` causes a SyntaxError.
2. **The `.sh` wrapper does NOT source `/opt/data/.env`** — GITHUB_TOKEN won't be available. Either source `.env` before calling the Python script directly, or patch the wrapper to add `source /opt/data/.env`.
3. **Root-owned files (mode 600) are skipped** — files in `skills/`, `memories/`, and `sessions/` owned by root with 600 permissions cannot be read by the hermes user and are silently skipped with a warning. This includes `.usage.json` and some `SKILL.md` files. To include them, they must be made readable (e.g., `sudo chmod u+r`).
4. **Working repo at `/opt/data/cache/sync-work/hermes-sync`** — this is the git working directory, NOT `/opt/data/hermes-sync/`.

**Token resolution order:**
1. `SYNC_REPO/netrc` (inside the git working dir)
2. `~/hermes-sync/netrc` (original location)
3. `$HERMES_HOME/.netrc`
4. `GITHUB_TOKEN` env var (from `.env`)

## What Gets Backed Up

| File/Dir | Destination | Notes |
|----------|-------------|-------|
| `config.yaml` | repo root | Main config |
| `SOUL.md` | repo root | Agent personality |
| `auth.json` | repo root | OAuth tokens |
| `kanban.db` | repo root | Task tracking |
| `state.db` + `-shm` + `-wal` | repo root | **All 3 files** for consistency |
| `.env` | `secrets/.env` | Encrypted API keys |
| `skills/` | `skills/` | Full skill library |
| `memories/` | `memory/` | Long-term memory |
| `sessions/` | `sessions/` | Session JSON + request dumps |
| `cron/jobs.json` | `cron/` | Job definitions |
| `plans/`, `hooks/`, `workspace/` | respective dirs | Various state |

## Excluded from Backup

`__pycache__`, `*.pyc`, `*.log`, `.git`, `node_modules`, `.venv`, `*.tmp`, `sync-work/`

## Secrets Encryption

`.env` is stored in `secrets/secrets.age` (encrypted) in the repo. The encryption passphrase is `dawnofdoyle` (PBKDF2-based Fernet).

## Repository Structure

```
ChonSong/hermes-sync/
├── config.yaml          # Main config
├── SOUL.md              # Personality
├── state.db*           # Session state
├── secrets/
│   ├── secrets.age     # Encrypted env vars
│   └── .env            # (decrypted at bootstrap)
├── skills/             # Skill library
├── memory/             # Memories
├── sessions/          # Session transcripts
├── cron/               # Job definitions
├── workspace/          # Working files
└── docker/
    └── docker-compose.yml
```

## Local Path Reference

| What | Path |
|------|------|
| Backup script (Python) | `/opt/data/scripts/hermes-backup.py` |
| Backup wrapper (bash) | `/opt/data/scripts/hermes-backup.sh` |
| Git working dir (inside container) | `/opt/data/cache/sync-work/hermes-sync/` |
| Sync repo (host) | `/home/sean/.hermes-sync/` |
| Sync repo (container, read-only) | `/opt/data/hermes-sync/` |
| Hermes home (container) | `/opt/data/` |
| Hermes home (host) | `/home/sean/.hermes/` |
| Backup log | `/opt/data/logs/hermes-backup.log` |
| Backups dir | `/opt/data/backups/` (used only with `--full-image`) |

## Common Issues

**Sync gap:** The watcher is event-based. If the watcher had a gap (e.g., process restart), changes during that window won't be pushed until the next change. To force a full sync, run the backup script manually.

**Git push fails:** Check git credentials. Token stored in:
1. `GITHUB_TOKEN` env var
2. `~/.netrc` (from `hermes-sync/netrc`)
3. `.env` with `GITHUB_TOKEN=...`

**Empty `/opt/data/backups/`:** This is correct — there is no local intermediate backup. Everything goes directly to GitHub via the sync mechanism.