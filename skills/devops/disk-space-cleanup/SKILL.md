---
name: disk-space-cleanup
description: Audit and reclaim disk space on Linux workstations and containers. Covers identification of disk hogs, safe deletion order (zero-risk → low-risk → rebuild-able), handling permission boundaries, and routine maintenance (git gc, cache clearing). Trigger when disk usage exceeds 85%, user asks to "save disk space", "clean up", or "free space", or when investigating "no space left on device" errors.
---

# Disk Space Cleanup

Audit and reclaim disk space methodically — identify, prioritize by risk, execute in safe order.

## Phase 0: Assess Overall State

```bash
df -h /                    # overall usage
```

**Thresholds:**
- < 85%: routine maintenance only
- 85–92%: active cleanup recommended
- > 92%: urgent — prioritize zero-risk deletions first

### ⚠️ Critical Impact: Hermes Session Failures

When disk usage exceeds 92%, the Hermes `state.db` (typically 1-2GB) becomes a bottleneck:
- SQLite operations time out — even `PRAGMA quick_check` can take >60s
- Session load/save operations fail silently, making it look like prompts "aren't responded to and immediately fail"
- The DB can't write WAL/journal files
- System swap thrashing compounds every DB call

**If you see this pattern** (broken sessions, immediate prompt failures, +92% disk):
1. Check `state.db` size: `ls -lh ~/.hermes/state.db`
2. Run `PRAGMA quick_check` — if it times out, the DB needs recovery
3. Follow `references/hermes-state-db-recovery.md` for recovery procedures
4. Free disk space FIRST (any means), then attempt VACUUM or prune

A 1.9GB state.db with 3,600+ sessions and 157K messages caused session failures in production. Pruning old sessions + VACUUM reduced it from 1.9GB to ~200MB.

## Phase 1: Identify Disk Hogs

Run these in order from coarse to fine:

```bash
# Per-directory breakdown (adjust paths for your mount layout)
du -sh /home/* /workspace/* /tmp/* /var/cache/* /var/log/* 2>/dev/null | sort -rh | head -30

# Hermes state.db — top disk hog candidate, often 1-2GB+
ls -lh ~/.hermes/state.db 2>/dev/null
# On host: ls -lh /home/<user>/.hermes/state.db

# Files larger than 50MB
find /home /workspace /tmp -xdev -type f -size +50M -exec du -sh {} \; 2>/dev/null | sort -rh | head -20

# node_modules directories
find /workspace -maxdepth 3 -name node_modules -type d -exec du -sh {} \; 2>/dev/null | sort -rh

# Python venvs
find /workspace -maxdepth 4 -name pyvenv.cfg -type f 2>/dev/null | while read f; do
  d=$(dirname $(dirname "$f"))
  echo "$d $(du -sh "$d" 2>/dev/null | cut -f1)"
done | sort -rh -k2

# .git directory sizes
find /workspace -maxdepth 3 -name .git -type d -exec du -sh {} \; 2>/dev/null | sort -rh

# Docker (if available)
docker system df 2>/dev/null
```

## Phase 2: Categorize by Risk

### Zero-risk (delete freely)
- `/tmp/npm-cache`, `/tmp/pip-cache` — package manager caches, rebuilt on next install
- `/tmp/test-clone*`, `/tmp/test-*` — old test artifacts
- Duplicate browser caches (e.g., `pw-browsers` vs `playwright_browsers` — check with `ls` to confirm identical contents, keep one)
- Stale project clones in `/tmp` (compare against `/workspace/` for the canonical copy)
- `node_modules` directories (rebuildable via `npm ci` if lockfile exists)

### Low-risk (verify first, then delete)
- `.bak` files — verify the live DB/data exists and is current before removing
- Old Hermes config backups (`/tmp/hermes-sync`) — verify current config is intact
- Stale build artifacts (`.next/cache`, webpack packs) — verify the app still builds

### Rebuild-able (delete when not actively developing)
- `node_modules` — `npm ci` restores from lockfile
- Python venvs — recreate from `requirements.txt`
- `.git` directories — only if you truly don't need history (rare)

### Never delete
- `/tmp/libs` containing Chrome/Puppeteer shared libraries (needed for browser automation)
- Active `.git` directories for projects you're working on
- Any file you haven't verified the contents/purpose of

## Phase 3: Execute in Safe Order

### Step 1 — Zero-risk tmp cleanup
```bash
rm -rf /tmp/npm-cache /tmp/pip-cache
rm -rf /tmp/test-clone* /tmp/test-*
# For duplicate browser caches, keep one:
rm -rf /tmp/playwright_browsers   # if pw-browsers is the canonical one
```

### Step 2 — Stale clones and backups
```bash
# Verify the canonical copy exists first
ls /workspace/gto-wizard-clone/HEAD 2>/dev/null && rm -rf /tmp/gto-wizard-clone

# Verify DB is loaded before deleting .bak
sqlite3 /workspace/forrest-plan-and-track/data/onetag.db 'SELECT COUNT(*) FROM sqlite_master WHERE type="table";'
# If that returns a number, the .bak is safe to delete (but check permissions — see below)
```

### Step 3 — git gc
```bash
cd /workspace && git gc --aggressive --prune=now
cd /workspace/<repo> && git gc --aggressive --prune=now
```

### Step 4 — Rebuild-able (only when not actively developing)
```bash
# node_modules
rm -rf /workspace/<project>/node_modules
# Later: cd /workspace/<project> && npm ci

# Python venvs
rm -rf /workspace/<project>/venv
# Later: python3 -m venv venv && pip install -r requirements.txt
```

## Permission Boundaries

**Check ownership before deleting:**
```bash
stat /path/to/file
```

If owned by `root` and you're running as non-root in a container:
- **You cannot delete it from the container.** Must be done from the host.
- Notify the user with the exact `sudo rm -rf` command to run on the host.
- Do NOT attempt `sudo` inside a container — it's almost never available.

**Pattern:**
```bash
# Check who you are
whoami && id

# If file is root-owned and you're not root:
# Tell user: "Run on host: sudo rm -rf /workspace/onetag.bak"
```

## Verification After Cleanup

```bash
df -h /
```

Report: before/after usage, what was deleted, what's pending (e.g., root-owned files needing host action).

## Routine Maintenance Schedule

| Task | Frequency | Command |
|------|-----------|---------|
| git gc on active repos | Weekly | `git gc --aggressive --prune=now` |
| Clear package caches | Monthly | `rm -rf /tmp/npm-cache /tmp/pip-cache` |
| Check state.db size | Weekly | `ls -lh ~/.hermes/state.db` — if >500MB, prune |
| State DB age analysis | Weekly | See `references/hermes-state-db-recovery.md` §5 |
| FTS index bloat check | Monthly | See `references/hermes-state-db-recovery.md` §6 |
| Empty session tab check | Monthly | See `references/hermes-state-db-recovery.md` §7 |
| Prune old sessions | Weekly | See `references/hermes-state-db-recovery.md` recovery options |
| Verify auto_prune is ON | After config changes | `grep auto_prune ~/.hermes/config.yaml` |
| Full disk audit | When >85% | This skill |

## Reference Files

- `references/hermes-state-db-recovery.md` — Full recovery procedures: FTS bloat, age analysis, tab leak detection, prune queries, VACUUM, dump/rebuild, prevention config
- `references/2026-06-06-disk-audit.md` — Prior disk audit from June 2026

## Common Pitfalls

- **Deleting `node_modules` without a lockfile** — always verify `package-lock.json` or `yarn.lock` exists first
- **Deleting `.git` for active repos** — you lose all local history and stashes
- **Assuming `/tmp` is safe** — check contents first; may contain active Puppeteer/Chrome libs needed for QA
- **Truncate-then-delete for large root-owned files** — `truncate` will also fail on permission denied; just report to user
- **Not checking for duplicates** — `pw-browsers` and `playwright_browsers` are often identical; `ls` both to confirm before deleting one
- **Don't declare a disk issue a blocker without context** — "96% used" sounds catastrophic but might mean 22GB free, which is workable. Always report BOTH percentage AND absolute free space. Flag + offer options (Google Drive offload, tmp cleanup) rather than saying "this blocks everything." The user values resourcefulness over alarm.
