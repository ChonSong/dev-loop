# Deploy Rollback Commit Loss — Recovery Pattern

## Problem

A deploy script that does `git fetch origin main && git reset --hard origin/main` (or similar) **destroys commits that exist only in the local repo**. If the Player committed but did not push, those commits become unreachable from any branch. They survive only in `git reflog`.

## Timeline of the Bug

1. Player commits locally (`f7dff07`) — not pushed
2. Deploy timer fires, pulls new remote commits, rolls back to the remote SHA
3. `git reset --hard origin/main` destroys the unreachable local commit
4. Player's commit is gone — not on any branch, not in origin

## Detection

Check if a commit exists and is reachable:

```
# Does the commit exist at all?
git cat-file -t <sha>       # returns "commit" if present

# Is it reachable from current HEAD?
git branch --contains <sha>  # empty = unreachable

# Reflog — the only lifeline
git reflog | head -10
```

## Recovery

```
# Cherry-pick the lost commit back onto main
git cherry-pick <sha>    # if the tree is clean

# If conflicts arise, resolve then:
git add -A && git cherry-pick --continue
```

If multiple consecutive commits were lost, cherry-pick the range:

```
git cherry-pick <oldest-sha>^..<latest-sha>
```

## Prevention

The player-agent workflow now mandates `git push origin main` immediately after every commit, before the deploy timer can fire. This ensures the commit is reachable from `origin/main` and cannot be destroyed by a rollback.

## Signals That a Rollback Occurred

- Deploy log shows "Rollback complete": `grep "Rollback" /home/sc/.hermes/logs/gto-wizard-deploy.log`
- Deploy service exited with status 1: `systemctl --user status gto-wizard-deploy.service`
- E2E tests failed during deploy (check log for "fail" or "✘")
- API returns 500 on previously working endpoints (old code re-deployed without the Player's fixes)
