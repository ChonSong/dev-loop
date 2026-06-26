# SSH Key Troubleshooting — Container to Host

## Symptom

```
ssh -i /home/hermeswebui/.hermes/container_key ...
Permission denied (publickey,password).
```

Or:

```
Warning: Identity file /home/hermeswebui/.hermes/container_key not accessible: No such file or directory.
```

## Root Causes

1. **Key file doesn't exist** — The path `/home/hermeswebui/.hermes/container_key` is the documented default but may not exist after container rebuilds.
2. **Wrong ownership** — Key exists but is owned by `root` and the cron runs as `hermes` (no read permission).
3. **No SSH agent** — No agent is running in the container; key must be specified via `-i`.

## Diagnostic Steps

```bash
# Check if the expected key exists
ls -la /home/hermeswebui/.hermes/container_key

# Search for any available keys
ls /home/hermeswebui/.ssh/
ls /home/hermes/.ssh/

# Check who you are
whoami

# Test connectivity (will fail but tells you which error)
ssh -i <key_path> -o BatchMode=yes -o ConnectTimeout=5 sean@172.19.0.1 "echo ok"
```

## Known Key Locations (varies by deployment)

| Path | Notes |
|---|---|
| `/home/hermeswebui/.ssh/id_ed25519` | **Current canonical** — referenced by `~/.ssh/config` `Host host` alias |
| `/home/hermeswebui/.ssh/config` | SSH config with `Host host` → `sean@172.19.0.1` — prefer `ssh host` over inline `-i` |
| `/home/hermeswebui/.hermes/container_key` | Legacy path — does NOT exist in current container |

## Resolution

1. **First try `ssh host`** — the SSH config (`~/.ssh/config`) defines a `Host host` alias pointing to `sean@172.19.0.1` with the correct identity file. This is the canonical method.
2. If `ssh host` fails, check the config file and the key it references.
3. If the key file doesn't exist, the cron job **cannot SSH to the host**. Report the failure and do not retry — the operator needs to mount or create the key.

## Affected Cron Jobs

Any cron job that uses `ssh ... sean@172.19.0.1` will fail, including:
- LinkedIn auto-post runner
- HWC service management jobs
- Any job requiring host-level commands (systemctl, Docker, builds)
