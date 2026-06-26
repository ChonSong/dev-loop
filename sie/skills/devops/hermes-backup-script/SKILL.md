---
name: hermes-backup-script
description: "hermes-backup.py and hermes-backup.sh — GitHub sync for /opt/data. Covers token lookup paths, HOME/env var requirements, and the container-vs-host execution environment distinction."
tags: [backup, github, git, sync, cron, container]
related_skills: [hermes-docker-sync-setup]
---

# hermes-backup-script

Git-based backup of Hermes state to the private `ChonSong/hermes-sync` GitHub repo. Two files involved:

| File | Role | Environment |
|------|------|-------------|
| `$HERMES_HOME/scripts/hermes-backup.py` | Python sync script (309 lines) | Container OR host |
| `$HERMES_HOME/scripts/hermes-backup.sh` | Bash wrapper (33 lines) | Container OR host (auto-detects) |

**Container paths (actual):**
- `HERMES_HOME=/home/hermeswebui/.hermes`
- Python: `/usr/local/bin/python3` (NOT `/usr/bin/python3`)
- Sync repo: `$HERMES_HOME/cache/sync-work/hermes-sync`
- Log: `$HERMES_HOME/logs/hermes-backup.log`

**Host paths (also valid):**
- `HERMES_HOME=/home/sc/.hermes`
- Python: `/home/sc/.hermes/hermes-agent/venv/bin/python3` (venv, not system)
- Sync repo: `$HERMES_HOME/cache/sync-work/hermes-sync`
- Log: `$HERMES_HOME/logs/hermes-backup.log`

**Cron job IDs:**
- Git sync: `2c60270a3745` (every 4h: 14:00, 18:00, 22:00 UTC)
- Docker image: `ad90af79146c` (daily 17:00 UTC)

## Token Lookup Order (hermes-backup.py)

`get_github_token()` searches these paths in order:

1. `SYNC_REPO/netrc` → `$HERMES_HOME/cache/sync-work/hermes-sync/netrc` (rarely exists)
2. `~/hermes-sync/netrc` → `~/.netrc` (expands via `os.path.expanduser`)
3. `HERMES_HOME/.netrc` → `$HERMES_HOME/.netrc`
4. `HERMES_HOME/home/.netrc` → `$HERMES_HOME/home/.netrc` (added 2026-05-29 — exists in container)
5. `~/.netrc` → `$HOME/.netrc`

## Key Env Vars

| Variable | Purpose | Container Value |
|----------|---------|-----------------|
| `HOME` | Controls where `~/.netrc` resolves | `/home/hermeswebui` (container default) |
| `HERMES_HOME` | The hermes state root | `/home/hermeswebui/.hermes` |
| `PYTHONUNBUFFERED=1` | Ensures stdout/stderr are not buffered (useful for cron log capture) | (always set) |

## Git Auth Architecture (Two Paths)

The backup script has **two separate credential paths** that must both work:

| Component | What it reads | Purpose |
|-----------|--------------|---------|
| `get_github_token()` | `$HOME/.netrc` | **Preflight gate** — script exits if this returns empty |
| `git push` / `git fetch` | `$HOME/.git-credentials` | **Actual auth** — git uses the credential helper `store` |

### Path 1: netrc (preflight gate)

`get_github_token()` searches for a line starting with `password` in these files:
1. `SYNC_REPO/netrc` → `$HERMES_HOME/cache/sync-work/hermes-sync/netrc`
2. `~/hermes-sync/netrc`
3. `HERMES_HOME/.netrc` → `$HERMES_HOME/.netrc`
4. `HERMES_HOME/home/.netrc` → `$HERMES_HOME/home/.netrc`
5. `~/.netrc` → `$HOME/.netrc`

Content format required:
```
machine github.com
login ChonSong
password ghp_abcdef123...
```

✅ Found at `$HERMES_HOME/home/.netrc` in the container

### Path 2: git credential store (actual auth)

Git is configured with `credential.helper=store`, which reads/writes `$HOME/.git-credentials`. This is what authenticates `git push origin master` to GitHub.

```bash
$ git config --global credential.helper
store
$ cat $HOME/.git-credentials
https://ChonSong:ghp_...@github.com
```

✅ Found at `/opt/data/home/.git-credentials` when `HOME=/opt/data/home`

### The `setup_repo()` Token Blindness Bug

```python
def setup_repo(token):
    repo_url = f"https://ChonSong:***@github.com/ChonSong/hermes-sync.git"
```

The `token` parameter is **never interpolated into the URL**. The URL has literal `***` as the password. Git authentication relies entirely on the credential helper store. The token from `get_github_token()` drives the preflight exit gate but is never used for actual auth.

**Practical impact:** If `$HOME/.git-credentials` has valid credentials but `$HOME/.netrc` is missing or malformed, git push works (path 2) but the script dies early with `[ERROR] No GitHub token found` (path 1). The two systems must both be functional for the script to succeed.

## Pitfall: Executing .sh Script with python3 Instead of bash

**Symptom:** `SyntaxError: invalid syntax` at line 6 (`export HOME=...`), exit code 1.

The bash wrapper (`hermes-backup.sh`) is a shell script. Running it with `python3` will always fail.

**Fix:**
```bash
# Correct invocation:
bash /home/hermeswebui/.hermes/scripts/hermes-backup.sh

# Or bypass the wrapper — call Python directly with proper env:
HERMES_HOME=/home/hermeswebui/.hermes /usr/local/bin/python3 /home/hermeswebui/.hermes/scripts/hermes-backup.py
```

## Pitfall: .env File Missing GITHUB_TOKEN

**Symptom:** `[ERROR] No GitHub token found` when running via the bash wrapper, even though `~/.netrc` exists with a valid token.

The bash wrapper sources `/opt/data/.env`:
```bash
set -a
. /opt/data/.env
set +a
```

If `.env` only has e.g. `OPENCODE_GO_API_KEY=...` but no `GITHUB_TOKEN=...`, the Python script's fallback `os.environ.get("GITHUB_TOKEN", "")` returns empty — and `get_github_token()` exits with an error before reaching the netrc search logic (it returns early via the env var check on line 54).

**Root cause:** The `GITHUB_TOKEN` may be stored in `$HERMES_HOME/cache/sync-work/hermes-sync/secrets/.env` (the repo secrets file) but NOT in `$HERMES_HOME/.env`. The bash wrapper only sources the latter.

**Fix option A — add GITHUB_TOKEN to .env:**
```bash
grep '^GITHUB_TOKEN=' /opt/data/cache/sync-work/hermes-sync/secrets/.env >> /opt/data/.env
```
This makes the variable available to both the bash wrapper's `source` and the Python script's `os.environ.get()`.

**Fix option B — source the secrets file too:**
In the bash wrapper, before the Python call:
```bash
. /opt/data/cache/sync-work/hermes-sync/secrets/.env 2>/dev/null || true
```

## Pitfall: .sh Wrapper Sets HOME to a Non-Container Path

**Status:** Fixed (2026-06-04). The wrapper now auto-detects container vs host. See "Shell Wrapper Auto-Detection" section above.

**Historical context:** The old wrapper hardcoded `export HOME=/home/sean` which broke inside the container. The double-bind (fix for container breaks host, and vice versa) is now resolved by auto-detection.

## The HOME Path Mismatch Trap

**Symptom:** `[ERROR] No GitHub token found`, exit_code: 1

The old wrapper hardcoded `export HOME=/home/sean` which exists on the **host** but NOT inside the **container**. When Python runs inside the container with `HOME=/home/sean`:
- `os.path.expanduser("~/.netrc")` → `/home/sean/.netrc` → **does not exist** inside container

**Status:** Fixed in the wrapper (auto-detects container vs host). The Python script's `HERMES_HOME/home/.netrc` fallback path also provides a safety net independent of `HOME`.

**Correct container cron command:**
```bash
HERMES_HOME=/home/hermeswebui/.hermes /usr/local/bin/python3 /home/hermeswebui/.hermes/scripts/hermes-backup.py
```

## Verified Successful Output

```
=== Hermes Backup — 2026-06-04 11:48 UTC+10:00 ===

[1/3] Repo setup...

[2/3] Syncing ALL data (no ignores)...
  ✓ config.yaml
  ✓ SOUL.md
  ✓ kanban.db
  ✓ state.db*
  ✓ .env → secrets/.env
  ✓ skills/
  ✓ memories/
  ✓ workspace/
  ✓ hooks/
  ✓ sessions/
  ✓ plans/
  ✓ cron/
  ✓ scripts/
      Total: 15 items

[3/3] Push to GitHub...
[OK] Pushed: auto-sync 2026-06-04T11:49:03+1000 (107 files)

[Docker] Skipped (use --full-image to include)

=== Done ===
```

## Shell Wrapper Auto-Detection (Fixed 2026-06-04)

The wrapper (`hermes-backup.sh`) now auto-detects its environment:

```bash
if [ -z "$HERMES_HOME" ]; then
    if [ -d /home/hermeswebui/.hermes ]; then
        export HERMES_HOME=/home/hermeswebui/.hermes   # container
    else
        export HERMES_HOME=/opt/data                    # host
    fi
fi
```

It also sets git identity before calling Python, so it works in both container and host contexts without pre-configuration.

**Correct invocation (container cron — preferred):**
```bash
HERMES_HOME=/home/hermeswebui/.hermes /usr/local/bin/python3 /home/hermeswebui/.hermes/scripts/hermes-backup.py
```

**Or use the wrapper (works in both environments):**
```bash
bash /home/hermeswebui/.hermes/scripts/hermes-backup.sh
```

**What Gets Synced**

Everything in `$HERMES_HOME/` except Docker images:
- `config.yaml`, `SOUL.md`, `auth.json`, `kanban.db`, `state.db`
- `.env` → backed up as `secrets/.env`
- `skills/`, `memories/`, `workspace/`, `hooks/`, `sessions/`, `plans/`, `cron/`, `scripts/`

## Pitfall: Git Identity Not Configured in Container (Silent Commit Failure)

**Symptom:** Backup script runs, copies all data items successfully, but push fails:
```
[WARN] commit: Author identity unknown
fatal: unable to auto-detect email address (got 'hermes@hpprobook.(none)')
```
Exit code is 0 (the script doesn't treat commit failure as fatal), so the cron job reports `status: ok` even though nothing was pushed.

**Root cause:** `setup_repo()` calls `git config --global user.email` and `git config --global user.name`, but inside the container these don't persist across cron invocations. Each cron run starts fresh with no git identity.

**Fix — set git identity in the container permanently:**
```bash
# Run once inside the container:
git config --global user.email "seanos1a@gmail.com"
git config --global user.name "Sean"
```

**Verification:** After setting identity, manually run the backup and confirm the push succeeds:
```bash
HERMES_HOME=/home/hermeswebui/.hermes /usr/local/bin/python3 /home/hermeswebui/.hermes/scripts/hermes-backup.py
# Should see: [OK] Pushed: auto-sync ... (N files)
```

**Detection:** Check `$HERMES_HOME/logs/hermes-backup.log` for `[WARN] commit: Author identity unknown`. If present, the last successful push is stale and the sync repo has uncommitted changes.

## Pitfall: Docker CLI Not Installed in Container

**Symptom (with `--full-image`):**
```
/usr/bin/bash: line N: docker: command not found
```

**Root cause:** The `docker` binary is not installed inside this container. The `--full-image` backup step calls `docker save` which requires the Docker CLI. Without it, the Docker backup step cannot run at all.

**Note:** This is distinct from the Docker socket permissions issue documented in `references/docker-socket-details.md`. That issue assumed the Docker CLI was present but couldn't access the socket. Here the binary itself is absent.

**To run Docker image backup, invoke the script via SSH to the host where Docker is installed:**
```bash
ssh root@172.17.0.1 "HERMES_HOME=/opt/data /opt/data/scripts/hermes-backup.py --full-image"
```

**Or add Docker CLI to container:**
```bash
apt-get update && apt-get install -y docker.io
```

**Verification:**
```bash
docker info --format '{{.ServerVersion}}' 2>&1 || echo "Docker CLI not available"
```

## Pitfall: Hardcoded Python Path in Shell Wrapper

**Symptom (host):** `hermes-backup.sh` exits 0 but does nothing. Log shows:
```
/home/sc/.hermes/scripts/hermes-backup.sh: line 29: /usr/local/bin/python3: No such file or directory
```

**Root cause:** The wrapper hardcoded `/usr/local/bin/python3` which exists inside the container but not on the host. The second `echo $?` line ensured the wrapper always exits 0 regardless.

**Fix (applied 2026-06-14):** The wrapper now searches for Python dynamically in priority order:
```bash
PYTHON=""
for p in "$HERMES_HOME/hermes-agent/venv/bin/python3" /usr/bin/python3 /usr/local/bin/python3; do
    if [ -x "$p" ]; then
        PYTHON="$p"
        break
    fi
done
if [ -z "$PYTHON" ]; then
    echo "No python3 found anywhere"
    exit 1
fi
"$PYTHON" "$HERMES_HOME/scripts/hermes-backup.py" "$@" >> "$LOG" 2>&1
```

This prefers the hermetic venv Python first (present on host), falls back to system paths. The script now works in both container and host environments without the wrapper needing to know which it's in.

**Known limitation:** The exit code masking pitfall below still applies — the trailing `echo` wraps the exit code. A future fix should capture `PY_EXIT=$?` and `exit $PY_EXIT`.

## Pitfall: `import json` Inside Empty For Loop (UnboundLocalError)

**Symptom (with `--full-image`):** Python script crashes at the Docker container-info step with:
```
UnboundLocalError: cannot access local variable 'json' where it is not associated with a value
```

Docker images DO save successfully before the crash. The error occurs only during the container-mounts-info step and is non-fatal to the image backup itself.

**Root cause:** `backup_docker_images()` had `import json` inside the `for name, path in containers:` loop body:
```python
containers = [("hermes", "/opt/data"), ("hermes-dashboard", "/opt/data/hermes-dashboard")]
for name, path in containers:
    import json            # ← never runs if containers list is empty
    info = json.loads(out)
    ...
# later...
json.dump(container_info, f, indent=2)   # ← UnboundLocalError
```

When no containers match (both `hermes` and `hermes-dashboard` don't exist on the host), the loop body never executes, `import json` never runs, and the module name `json` is unbound as a local variable at the dump call site.

**Fix (applied 2026-06-14):** Moved `import json` to the top of `backup_docker_images()`, outside any loop. Now `json` is always available regardless of whether containers are found.

**Related detection:** A successful Docker image backup with a crash at the very end (container-info write) is a strong indicator of this bug.

## Pitfall: Shell Wrapper Masks Python Exit Code

**Symptom:** The Python backup script fails (e.g., `[ERROR] clone failed: ...`) but the cron job reports `status: ok` with exit code 0. No one notices the backup hasn't actually pushed anything for days.

**Root cause:** The shell wrapper (`hermes-backup.sh`) ends with:
```bash
/usr/local/bin/python3 "$HERMES_HOME/scripts/hermes-backup.py" "$@" >> "$LOG" 2>&1
echo "$(date '+%Y-%m-%d %H:%M:%S') backup exit: $?" >> "$LOG"
```

The second line (`echo ... $?`) always **succeeds** — its exit code (0) becomes the overall exit code of the wrapper regardless of whether the Python script above it failed. So cron sees exit code 0 for every run.

The Python script does correctly call `sys.exit(1)` on failures (no token, git auth failure, push failure), but the shell wrapper never propagates those exit codes.

**Consequences:**
- Failed backup → cron sees `status: ok`
- Stale data on GitHub grows stale silently
- Only manual log inspection reveals failures
- Log shows `backup exit: 0` even when Python printed `[ERROR]` above it

**Detection:**
```bash
grep -E '\[ERROR\]' "$HERMES_HOME/logs/hermes-backup.log" | tail -10
```

**Temporary workaround — run Python directly (bypasses wrapper):**
```bash
HERMES_HOME=/home/hermeswebui/.hermes /usr/local/bin/python3 /home/hermeswebui/.hermes/scripts/hermes-backup.py
# Exit code reflects actual success/failure
```

**Permanent fix needed:** Change the wrapper to propagate the exit code:
```bash
/usr/local/bin/python3 "$HERMES_HOME/scripts/hermes-backup.py" "$@" >> "$LOG" 2>&1
PY_EXIT=$?
echo "$(date '+%Y-%m-%d %H:%M:%S') backup exit: $PY_EXIT" >> "$LOG"
exit $PY_EXIT
```

## Pitfall: GitHub Token Expiry Detection

**Symptom:** Backup script fails at `setup_repo()` step with:
```
[WARN] fetch failed: remote: Invalid username or token
fatal: Authentication failed for 'https://github.com/ChonSong/hermes-sync.git/'
[ERROR] clone failed: ... remote: Invalid username or token ...
```

**Root cause:** The GitHub classic token (`ghp_...`) stored in `$HERMES_HOME/home/.netrc` has been invalidated (expired, revoked, or permissions changed). The script's `get_github_token()` finds it in the netrc file, passes the preflight check, but git operations fail because the token itself no longer authenticates.

**How to test a token is valid:**
```bash
TOKEN=$(grep password ~/.netrc | awk '{print $2}')
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: token $TOKEN" https://api.github.com/user)
# 200 = valid, 401 = expired/revoked, 403 = rate limited
```

**Action to recover — generate a new token:**
1. Go to https://github.com/settings/tokens
2. Generate a new classic token with `repo` scope (full control of private repos) or a fine-grained token with contents:write + metadata:read for the `ChonSong/hermes-sync` repo
3. Update the token in both files:
   - `$HERMES_HOME/home/.netrc` (primary, used by script)
   - `$HERMES_HOME/hermes-sync/netrc` (backup, if sync repo is still cloned)
4. Run the script directly to verify:
   ```bash
   HERMES_HOME=/home/hermeswebui/.hermes /usr/local/bin/python3 /home/hermeswebui/.hermes/scripts/hermes-backup.py
   ```

**Netrc file format (must be exact):**
```
machine github.com
login ChonSong
password ghp_YOUR_NEW_TOKEN_HERE
```

## Pitfall: Memory Curation Cron Job Writes to Wrong Path

**Symptom:** Memory curation cron job runs but MEMORY.md is never updated. No error visible.

**Root cause:** The curation job prompt references `/workspace/MEMORY.md` as the output path. The `/workspace` directory is NOT writable from inside the hermes container (it either doesn't exist or is read-only). The job silently fails or writes to a path that doesn't persist.

**Fix:** Write MEMORY.md to `/opt/data/MEMORY.md` instead. This is the persistent data directory that IS writable from the container.

```bash
# Correct path for memory files inside the container:
/opt/data/MEMORY.md          # Long-term curated memory
/opt/data/memory/YYYY-MM-DD.md  # Daily logs
```

**Also:** The curation job should use `session_search` as its primary data source (not filesystem scanning), since session transcripts are the authoritative record of what happened.

**Detection:** Check if `/workspace/MEMORY.md` exists and has recent content. If missing or stale, the curation job has been failing silently.

## Pitfall: SSH Target for Host Commands Changed

**Symptom:** Cron jobs that SSH to the host fail with "Connection refused" or "Host key verification failed."

**Root cause:** The SSH target `sean@localhost` no longer works from inside the container. The host's SSH configuration or user setup changed.

**Fix:** Use `root@172.17.0.1` (the Docker gateway IP) instead:

```bash
# Old (broken):
ssh sean@localhost "command"

# New (working from container):
ssh root@172.17.0.1 "command"
```

**Affected jobs:** Tunnel watchdog, backup sync, and any cron job that SSHes to the host.

## Related

- `hermes-docker-sync-setup` — umbrella skill for the full hermes-sync setup
- `go` — Go build/test patterns (updated 2026-06-08: SSH broken, build in-container)
- `hermes-backup.log` at `$HERMES_HOME/logs/hermes-backup.log` — execution log
- `references/docker-socket-details.md` — Docker socket GID/group diagnostics for this container
- `references/token-expiry-diagnostics.md` — 2026-06-12: expired GitHub token reproduction recipe
- GitHub repo: `https://github.com/ChonSong/hermes-sync` (private, classic PAT in netrc)

## Pitfall: Cron Job Prompt References Wrong Path

**Symptom:** Cron job runs but the agent can't find the backup script.

**Root cause:** The cron job prompt referenced `/opt/data/scripts/hermes-backup.sh` which doesn't exist inside the container. The actual path is `/home/hermeswebui/.hermes/scripts/hermes-backup.sh`.

**Fix:** Update cron job prompts to use the correct container path and invoke Python directly:
```
HERMES_HOME=/home/hermeswebui/.hermes /usr/local/bin/python3 /home/hermeswebui/.hermes/scripts/hermes-backup.py
```

**Cron job IDs to update:**
- Git sync: `2c60270a3745`
- Docker image: `ad90af79146c` (add `--full-image` flag)