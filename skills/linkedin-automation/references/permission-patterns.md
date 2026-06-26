# Container/Host Permission Debugging Patterns

## The Problem

The Hermes container runs as `hermeswebui` (uid 1000). Some files on its mounted ext4 partition (`/dev/sda2`) are owned by root (uid 0), created by the container entrypoint before privilege drop. The container has no root access.

## Symptoms

- `Permission denied` on files like `~/.hermes/cron/jobs.json`
- `chmod`/`chown` fail with `Operation not permitted` from inside container
- `su root` fails with `Authentication failure`
- `prctl` to raise ambient capabilities returns `EPERM`

## Fix Methods (in order of preference)

### Method 1: docker exec as root (BEST)
```bash
# From HOST — enter container as root
docker exec -u root -it <container_name> chmod 666 /path/to/file
docker exec -u root -it <container_name> chown 1000:1000 /path/to/file
```
Requires: user has `docker` group membership or sudo to docker.

**Note:** SSH container user can run `docker exec` IF they can authenticate to the Docker socket. On this setup, SSH as `sean@172.19.0.1` + `docker exec -u root <container>` works because `sean` is in the docker group.

### Method 2: Fix from host filesystem
```bash
# Find the actual mount path on host
# /home/hermeswebui/.hermes on container → /opt/data/home/.hermes on host (example)
sudo chmod 666 /host/path/to/file
```
The host path and container path are DIFFERENT. Check `mount` inside container to find the device, then find the host-side path.

### Method 3: Modify container entrypoint
Add to Dockerfile or compose:
```yaml
# Add startup command that fixes permissions
command: >
  sh -c "chown -R hermeswebui:hermeswebui /home/hermeswebui/.hermes && exec hermes"
```
Or set `user: root` in compose and have entrypoint drop privileges after fixing ownership.

## Key Gotchas

1. **Container uid != host uid.** `hermeswebui` (uid 1000) exists in container's `/etc/passwd` but NOT in host's. Files owned by uid 1000 on ext4 are owned by hermeswebui — but `chown hermeswebui:hermeswebui` fails on host because that name doesn't exist there. Use numeric: `chown 1000:1000`.

2. **Capabilities in bounding set != effective.** Container may have `CAP_DAC_OVERRIDE` in bounding set (`CapBnd`) but NOT in effective set (`CanEff`). `prctl(PR_CAP_AMBIENT_RAISE)` returns EPERM. The capabilities are only available if the container was launched with `--cap-add`.

3. **`scp` to host workspace fails** if file ownership lands differently. Use `/tmp/` on host as transfer point — it's world-writable.

4. **f-strings in SSH inline Python break** when containing nested `{}` or `""` quotes. The `ssh "python3 -c \"...f{var}...\""` pattern is fragile. Always write scripts to a file first, `scp` them, then execute.

5. **SSH `-t` for pseudo-terminal** — needed for `sudo` over SSH. But some SSH backends (like Hermes terminal tool) don't allocate PTY even with `-t`. In that case, the `docker exec -u root` approach is more reliable.

## Files That Tend to Be Root-Owned

- `~/.hermes/cron/jobs.json` — created by hermes-agent entrypoint
- Any file in `~/.hermes/` created before privilege drop
- SQLite databases initialized at container start
