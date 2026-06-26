# Cron DB Permission Fix (Docker Container Context)

## Symptom
`cronjob` tool fails with "Permission denied" on `/home/hermeswebui/.hermes/cron/jobs.json`.

## Root Cause
The Hermes container entrypoint creates the cron DB as root, then drops to `hermeswebui` (uid 1000). The file is on a dedicated ext4 partition (`/dev/sda2`) that preserves Unix permissions. Inside the container, you cannot `chmod` or `chown` it.

## Fix

```bash
# From the HOST machine — replace container name if different:
docker exec -u root hermes-webui-hermes-webui-1 chmod 666 /home/hermeswebui/.hermes/cron/jobs.json

# Verify from inside the container:
ls -la /home/hermeswebui/.hermes/cron/jobs.json
# Should show: -rw-rw-rw- 
```

## Why Not Other Approaches
- `chmod` from inside container → EPERM (not root)
- `su - root` → requires password, not set
- Ambient capabilities (`CAP_DAC_OVERRIDE`) → in bounding set but not effective; `prctl` returns EPERM
- Editing `~/.hermes` path directly → path doesn't exist in container (it's on host at `/opt/data/home/`)
- SSH + sudo → needs PTY + password; `ssh -t` not available from container terminal

## Prevention
Add to container startup or entrypoint:
```bash
# After creating cron DB:
chown hermeswebui:hermeswebui /home/hermeswebui/.hermes/cron/jobs.json
chmod 666 /home/hermeswebui/.hermes/cron/jobs.json
```
