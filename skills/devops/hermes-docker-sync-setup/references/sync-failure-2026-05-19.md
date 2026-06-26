# Sync Failure — May 19 2026

## Problem

Push to `hermes-sync` failed:
```
remote: error: File state.db.gz is 162.11 MB; this exceeds GitHub's file size limit of 100.00 MB
GH001: Large files detected.
```

Also: `Permission denied` on `config.yaml` — container writes as root, host cron runs as sean.

## Resolution

1. **Exclude `*.gz` and `state.db*`** from repo via `.gitignore`:
   ```
   *.gz
   state.db
   state.db-shm
   state.db-wal
   ```

2. **History rewrite** (file was already committed and cached in GitHub objects):
   ```bash
   cd /home/sean/.hermes/cache/sync-work/hermes-sync
   git filter-branch --force --index-filter "git rm --cached --ignore-unmatch state.db.gz" --tag-name-filter cat -- --all
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive
   git push origin master --force
   ```

3. **Update `sync-cron.sh`** to include all subdirs + `cache/` in permissions chmod:
   ```bash
   chmod -R a+rX \
     $HERMES_HOME/sessions $HERMES_HOME/skills $HERMES_HOME/memory \
     $HERMES_HOME/memories $HERMES_HOME/cron $HERMES_HOME/workspace \
     $HERMES_HOME/hooks $HERMES_HOME/plans \
     $HERMES_HOME/hermes-agent $HERMES_HOME/cache $HERMES_HOME/scripts
   ```

4. **Sync path verified** (failed initially on wrong path):
   - Wrong: `/opt/data/.hermes/hermes-sync/scripts/sync-cron.sh`
   - Correct: `/home/sean/.hermes/scripts/sync-cron.sh`
   - Working dir: `/home/sean/.hermes/cache/sync-work/hermes-sync/`

5. **Result**: Exit 0, `[OK] No changes — already in sync`

## Key facts

- Host: EndeavourOS (Arch-based), SSH at `172.19.0.1` (not localhost)
- Container runs hermes via Docker; SSH access from container to host via key at `/home/hermeswebui/.hermes/container_key`
- `hermes-sync` = `ChonSong/hermes-sync` private repo on GitHub
- `hermes-agent` local working copy at `/home/hermeswebui/.hermes/hermes-agent`
- `hermes-sync-backup.py` path: `/home/sean/.hermes/scripts/hermes-sync-backup.py`
- Log: `/home/sean/.hermes/logs/sync-backup.log`

## Outstanding: state.db backup

state.db is NOT in the sync. On a new machine it will be empty. If session history matters, add rclone to Google Drive in `sync-cron.sh` or a separate cron job. rclone is at `/usr/bin/rclone` with config at `/opt/data/rclone_config/rclone.conf`.