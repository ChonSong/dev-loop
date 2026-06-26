# Disk Management — Recovery & Prevention

## Measured Space Facts

| Metric | Value |
|--------|-------|
| Host disk (`/dev/sda2`) | ~461GB total |
| After cleanup | ~22GB free (~96% full) |
| Single prune pass | ~37-80GB freed |
| Single npm install + uv pip install | Can fill disk again |
| Docker image backup (compressed) | ~1.3GB |

## Full Disk Recovery Sequence

Run from `/opt/data` (inside container) or from host:

```bash
# Step 1: Prune Docker images/build cache
ssh -i /opt/data/home/.hermes/home/.ssh/id_ed25519 sean@localhost "docker image prune -f && docker builder prune -af"

# Step 2: If still full, restart postgres then prune again
ssh -i /opt/data/home/.hermes/home/.ssh/id_ed25519 sean@localhost "docker restart agent-os-postgres && sleep 5 && docker image prune -f"

# Step 3: Verify
ssh -i /opt/data/home/.hermes/home/.ssh/id_ed25519 sean@localhost "df -h / | tail -1"
```

**Why restart postgres first:** Docker pruning while postgres is under load can cause I/O contention. Restarting postgres forces a clean checkpoint and frees up write buffers before pruning.

## Preventing Disk Full During Builds

1. **Run prune before building** if disk is above 90%:
   ```bash
   ssh ... "docker builder prune -af && docker image prune -f"
   ```

2. **Monitor during build** — if build succeeds but space is critically low, prune immediately post-build:
   ```bash
   ssh ... "docker builder prune -af"
   ```

3. **The hermes-sync Docker image backup** (~1.3GB) runs at 7am AEST. If disk is tight before a planned build, manually trigger the prune first.

## Docker Image Backup Location

`/opt/data/backups/docker-images.tar.gz` — this tarball is included in the git sync at the next scheduled run (every 6 hours). It is NOT excluded from the backup.

The backup includes:
- `hermes-sync_latest.tar`
- `ghcr.io_chonsong_agent-os_latest.tar`
- `postgres_16-alpine.tar`
- `container-info.json`

## What's Safe to Delete Inside Container

| Path | Type | Safe to Delete |
|------|------|---------------|
| `/tmp/*` | Temp files (browser caches, camoufox) | ✅ Yes |
| `/opt/data/backups/*.tar.gz` | Old Docker image backups | ✅ Yes (new one created on backup run) |
| `*/node_modules` | Build artifacts | ✅ Yes (regenerated on rebuild) |
| `*/__pycache__`, `*.pyc` | Python cache | ✅ Yes |
| `*.log` | Log files | ✅ Yes |

## What's NOT Safe to Delete

- `state.db*` — Hermes session state
- `state.db-shm`, `state.db-wal` — SQLite WAL files (delete causes corruption)
- `.git/` directories — repo metadata
- `/opt/hermes/` — Hermes installation (regenerating takes 15-20 min)