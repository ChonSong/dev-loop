# Token Expiry Diagnostics — 2026-06-12

Recorded during a failed cron backup run (2026-06-12 03:04 UTC+10:00).

## Symptom

```
=== Hermes Backup — 2026-06-12 03:04 UTC+10:00 ===

[1/3] Repo setup...
[WARN] fetch failed: remote: Invalid username or token. Password authentication is not supported for Git operations.
fatal: Authentication failed for 'https://github.com/ChonSong/hermes-sync.git/', re-cloning
[ERROR] clone failed: Cloning into '/home/hermeswebui/.hermes/cache/sync-work/hermes-sync'...
remote: Invalid username or token. Password authentication is not supported for Git operations.
fatal: Authentication failed for 'https://github.com/ChonSong/hermes-sync.git/'
```

## Diagnosis

1. **Token check** — The `GITHUB_TOKEN` env var was set, but the Python script's `get_github_token()` found the **expired** token in `$HERMES_HOME/home/.netrc` first. The script prefers netrc over `os.environ.get("GITHUB_TOKEN")`.

2. **API test** — Tested against `https://api.github.com/user` with `Authorization: token <token>`:
   - Returned **401 Unauthorized**
   - Classic PAT (`ghp_...`) was expired/revoked

3. **Docker check** — `docker` CLI binary was not installed in the container at all (`command not found`). The `--full-image` flag passed to the wrapper could never have worked from inside the container.

4. **Exit code masking** — The shell wrapper (`hermes-backup.sh`) ended with `echo "backup exit: $?" >> "$LOG"` which always exits 0, so the cron job reported success despite the Python script failing at step 1/3.

## Token Locations Checked

| File | Exists | Content |
|------|--------|---------|
| `$HERMES_HOME/home/.netrc` | ✅ | `ghp_Sn...Wxdd` (expired) |
| `$HERMES_HOME/hermes-sync/netrc` | ✅ | Same expired token |
| `$HERMES_HOME/.netrc` | ❌ | — |
| `~/.netrc` | ❌ | — |
| `GITHUB_TOKEN` env var | ✅ | Set but not used (netrc takes priority) |

## Recovery Steps

1. Generate new classic PAT at https://github.com/settings/tokens with `repo` scope
2. Replace in `$HERMES_HOME/home/.netrc`
3. Replace in `$HERMES_HOME/hermes-sync/netrc`
4. Run verification: `HERMES_HOME=/home/hermeswebui/.hermes /usr/local/bin/python3 /home/hermeswebui/.hermes/scripts/hermes-backup.py`
