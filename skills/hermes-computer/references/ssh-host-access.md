# SSH to Host (EndeavourOS)

## Connection Details

- **Host:** `172.19.0.1` (Docker bridge gateway)
- **User:** `sean`
- **Key:** `~/.ssh/id_ed25519` (labeled "hermes-container")
- **Port:** 22
- **Host key:** ed25519 — fingerprint matches `/etc/ssh/ssh_host_ed25519_key.pub`

## Adding to known_hosts

```bash
ssh-keyscan -t ed25519 172.19.0.1 >> ~/.ssh/known_hosts
```

## Verifying

```bash
ssh sean@172.19.0.1 "hostname"
# → hpprobook
```

## What Works Via SSH

- Running host `google-chrome-stable` for screenshots
- Checking HWC server health: `curl -sf http://localhost:3005/`
- Starting/restarting HWC server: `cd ~/hermes-web-computer && HERMES_HWC_ROOT=... nohup agent-os server --port 3005 &`
- Copying files between container and host via pipes

## Path Mapping

| Context | Path |
|---------|------|
| Container | `/home/hermeswebui/` |
| Host | `/home/sean/` |
| HWC repo (host) | `/home/sean/.hermes/hermes-web-computer` |
| HWC repo (container) | `/home/hermeswebui/.hermes/hermes-web-computer` (read-only sync) |
| QA screenshots | `/tmp/hwc-qa/` (both) |
| Visual QA script (host) | `~sean/.hermes/scripts/hwc-host-visual-qa.sh` |
| Visual QA script (container wrapper) | `~/.hermes/scripts/hwc-visual-qa.sh` |

## Cron Integration

Container cron `fcf273002361` runs `hwc-visual-qa.sh` which SSHs to host and delegates to `hwc-host-visual-qa.sh`. This is the no_agent watchdog pattern — runs every 720m, silent on pass, alerts on fail.
