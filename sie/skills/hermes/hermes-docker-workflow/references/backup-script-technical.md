# Backup Script Technical Reference

## Key Discovery: Read-Only Mount

The hermes-sync volume mounts as **read-only** inside the container:
```
/dev/sda2 on /opt/data/hermes-sync type ext4 (ro,noatime)
```

All backup writes MUST go to the **writable git working copy** at:
```
/opt/data/cache/sync-work/hermes-sync/
```

Do NOT attempt to write to `/opt/data/hermes-sync/` directly — it will fail with `OSError: read-only file system`.

## Script Location

- Main script: `/opt/data/scripts/hermes-backup.py`
- Cron wrapper: `/opt/data/scripts/hermes-backup.sh`
- Log output: `/opt/data/logs/hermes-backup.log`

## Git Config Required

The backup script runs `git config --global --add safe.directory /opt/data/hermes-sync` to handle git's "dubious ownership" error when the working directory is owned by a different user than the git process.

## Key Script Variables

```python
HERMES_HOME  = Path("/opt/data")
SYNC_REPO    = HERMES_HOME / "cache" / "sync-work" / "hermes-sync"  # writable
CONFIG_DIR   = HERMES_HOME / "config"  # NOT SYNC_REPO / "config"
BACKUP_DIR   = Path("/opt/data/backups")
```

**Critical fix discovered:** Config files (`config.yaml`, `SOUL.md`, etc.) must be sourced from `HERMES_HOME / "config"`, NOT from `SYNC_REPO / "config"` (which points to the read-only mount). The script patches this during backup.

## Docker Image Backup Binary Handling

`docker save` outputs binary tar data. When captured as text, it causes:
```
'utf-8' codec can't decode byte 0x8b
```

**Fix:** Use `subprocess.run()` with `stdout=None` (inherit) or write to a temp file with `-o tmp_file`. Never capture docker save output as text. The backup script uses:
```python
subprocess.run(
    ["docker", "save", "-o", str(backup_dir / f"{name}.tar"), image],
    stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
)
```

## Cron Schedule (Hermes Agent Cron, Not System Cron)

The container has NO cron daemon. Backups run as Hermes agent-side cron jobs:

| Job ID | Schedule | Action |
|--------|----------|--------|
| `2c60270a3745` | UTC 21,03,09,15 (7am/1pm/7pm/1am AEST) | Git sync only |
| `ad90af79146c` | UTC 21 daily (7am AEST) | Full Docker image backup |

Jobs execute the shell wrapper which sets Python path and redirects output.

## Full Image Backup Verification

After a full backup run, verify with:
```bash
ssh -i ... sean@localhost "ls -lh /opt/data/backups/docker-images.tar.gz"
# Expected: ~1.3GB

# Check what's inside
ssh -i ... sean@localhost "tar -tzf /opt/data/backups/docker-images.tar.gz | head -20"
# Expected: hermes-sync_latest.tar, ghcr.io_chonsong_agent-os_latest.tar, postgres_16-alpine.tar, container-info.json
```

## Git Push Verification

Check last commit:
```bash
cd /opt/data/cache/sync-work/hermes-sync && git log -1 --oneline
# Expected: auto-sync YYYY-MM-DDTHH:MM:SS+1000
```

Check push:
```bash
cd /opt/data/cache/sync-work/hermes-sync && git status
# Expected: "Your branch is up to date with 'origin/main'"
```