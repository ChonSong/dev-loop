# Bootstrap Failure: Stale Remote Divergence

## Problem

After a force-push that rewrote `hermes-sync` history (to remove `state.db.gz`), the bootstrap on a secondary machine failed with:
```
open /home/codespace/hermes-sync/docker/docker-compose.yml: no such file or directory
```

The `docker/` directory existed on the **host machine** (`bda234f`) but was missing from the **remote** (`fd76834`) because the host had force-pushed `fd76834` as the new remote HEAD before the `docker/` files were committed locally. The remote was ahead of what the bootstrap machine had cloned.

## Why It Happens

When you force-push a rewritten history to GitHub, any machine that cloned the repo **before** the force-push still has the old remote state cached. `git clone` fetches whatever `HEAD` is at the time — it doesn't know the remote will be later rewritten.

On a **fresh machine** (no prior clone), `git clone` always gets the true remote HEAD — including `docker/`. On a **stale machine** (cloned before the rewrite), `git pull` may succeed but leave the working tree at a commit (`fd76834`) that pre-dates the divergence.

## Symptoms

- Bootstrap fails at `docker compose -f docker/docker-compose.yml` — file not found
- `docker/` directory missing from clone but present on original machine
- `git status` shows nothing to commit, `git log --oneline` shows fewer commits than origin/main
- `git ls-tree HEAD` shows no `docker/` files but `git ls-tree origin/master` shows them

## Diagnosis

```bash
# On the failing machine:
cd ~/hermes-sync
git log --oneline -3 && echo "---" && git ls-tree HEAD --name-only | grep "^docker/" && echo "---remote---" && git ls-tree origin/master --name-only | grep "^docker/"
```

If local `HEAD` lacks `docker/` but `origin/master` has it → stale remote divergence.

## Fix

The cleanest fix is a fresh clone on stale machines:

```bash
# Nuclear but reliable — wipe and re-clone to get true remote HEAD
rm -rf ~/hermes-sync
git clone https://github.com/ChonSong/hermes-sync.git ~/hermes-sync
```

Alternatively, hard-reset to origin/master:
```bash
cd ~/hermes-sync
git fetch origin
git reset --hard origin/master
```

The `rm -rf` approach is preferred for bootstrap scenarios where you want zero ambiguity about which version you're installing.

## Prevention for Bootstrap Machines

For machines running `setup.sh` (fresh installs), the script always does a clean clone — no divergence possible.

For machines that ran an older `setup.sh` and are re-running (e.g. after a config update), consider adding this to the bootstrap:
```bash
# In setup.sh — ensure clean slate before clone
if [ -d "$HERMES_SYNC_DIR" ]; then
    # Check if local HEAD matches origin/master — force reset if diverged
    cd "$HERMES_SYNC_DIR"
    git fetch origin
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse origin/master)
    if [ "$LOCAL" != "$REMOTE" ]; then
        echo "Local diverged from remote — resetting to origin/master"
        git reset --hard origin/master
    fi
fi
```

## Summary

| Scenario | Result |
|----------|--------|
| Fresh machine clone | ✅ Always gets true remote HEAD |
| Stale clone + `git pull` | ⚠️ May land on old local HEAD if pull fails to fast-forward |
| Stale clone + `git reset --hard origin/master` | ✅ Gets true remote HEAD |
| `rm -rf` + re-clone | ✅ Guaranteed clean slate |

**Key insight:** The bootstrap's one-command `curl | bash` pattern is resilient **only** on fresh machines. On machines that have previously cloned `hermes-sync`, re-running the bootstrap may hit stale content. The fix is `rm -rf ~/hermes-sync` before re-running.