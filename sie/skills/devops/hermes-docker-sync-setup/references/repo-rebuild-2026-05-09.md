# Hermes-Sync Repo Rebuild — 2026-05-09

## What happened
1. Git permission error: `.git/objects` owned by root (container ran git commands as uid 0). Fixed with privileged alpine container `chown -R 1000:1000`.
2. `git pull` succeeded but repo had state.db (269MB) in git history from old syncs.
3. `git filter-branch` to purge state.db timed out after 180s (too many objects).
4. **Nuclear option**: Deleted GitHub repo via API, recreated fresh, built clean single-commit repo manually.

## Steps to rebuild clean repo
```bash
# 1. Delete old repo
curl -X DELETE -H "Authorization: token $TOKEN" https://api.github.com/repos/ChonSong/hermes-sync

# 2. Create fresh
curl -X POST -H "Authorization: token $TOKEN" -H "Content-Type: application/json" \
  https://api.github.com/user/repos -d '{"name":"hermes-sync","private":true}'

# 3. Build clean local repo
mkdir /tmp/hermes-sync-clean && cd /tmp/hermes-sync-clean
git init && git config user.email "..." && git config user.name "..."
# Copy all state files (NOT state.db raw, use .gz)
# Copy skills/, sessions/, memory/, cron/, scripts/, etc.
git add -A && git commit -m "initial: hermes state backup"
git remote add origin https://ChonSong:$TOKEN@github.com/ChonSong/hermes-sync.git
git push -f origin master

# 4. Move to sync-work location
mv /tmp/hermes-sync-clean /home/sean/.hermes/cache/sync-work/hermes-sync
```

## Disk cleanup results
- Docker prune: freed 15GB (53GB reclaimable images + 46GB build cache)
- Old hermes-agent source: freed 299MB
- Project clones in hermes-sync source: freed 836MB
- Total: 95% → 90% disk usage (461G total, ~46G free)

## Sync script patches applied
- state.db: gzip compress instead of skip (269MB → 94MB)
- sync-cron.sh: added `chmod -R a+r` before sync to handle root-owned container files
- Cron schedule: changed from `*/12` to `*/6` hours

## Key lesson
Never let a >100MB file into git history. Once it's in objects, `filter-branch` is too slow. Nuke and rebuild is faster.
