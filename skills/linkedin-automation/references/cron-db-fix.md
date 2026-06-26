# Cron DB Permission Fix

The Hermes cron database is root-owned by the Docker entrypoint. The `cronjob` tool fails with "Permission denied" when trying to read or write it.

## Diagnosis

```bash
# Check ownership
ls -la /home/hermeswebui/.hermes/cron/jobs.json
# output: -rw------- 1 root root 26410 May 31 00:49 jobs.json
```

## Fix (run on HOST)

```bash
docker exec -u root hermes-webui-hermes-webui-1 chmod 666 /home/hermeswebui/.hermes/cron/jobs.json
```

## Why Other Approaches Fail

| Approach | Why It Fails |
|----------|-------------|
| `chmod` from inside container | EPERM — we're `hermeswebui` (uid 1000), not root |
| `su - root` in container | Requires root password |
| Ambient capabilities (`prctl`) | CAP_DAC_OVERRIDE in bounding set but not effective; kernel returns EPERM |
| Editing `/opt/data/home/` path | Path doesn't exist in the container |
| SSH + sudo from container | Needs PTY + password; not available |
| `docker exec -u root` without `-t` | Works for simple commands but not interactive ones |

## Gotcha: Host vs Container Paths

`/opt/data/home/.hermes/cron/jobs.json` (on host) ≠ `/home/hermeswebui/.hermes/cron/jobs.json` (in container). They are different paths. Fixing one does NOT fix the other. You must enter the container as root to fix the container-side path.

## Verification

After fix:
```bash
ls -la /home/hermeswebui/.hermes/cron/jobs.json
# Should show: -rw-rw-rw- or similar (not root-owned 0600)
```
Then `cronjob(action='list')` should succeed.
