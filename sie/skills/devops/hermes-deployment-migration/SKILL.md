---
name: hermes-deployment-migration
description: Migrate Hermes Agent between deployment modes — Docker container ↔ native host (systemd user services). Covers mode detection, systemd service setup, cron job/script path migration, and companion container SSH configuration.
---

# Hermes Deployment Migration

Migrate a running Hermes Agent from Docker container to native host (systemd user services). The config persists via bind mounts, so the main work is fixing cron jobs and scripts that reference container-only paths.

## Detection

Check whether you're in a container or on the host:

```bash
ls /.dockerenv 2>/dev/null && echo "INSIDE CONTAINER" || echo "ON HOST"
docker ps --format '{{.Names}}' | grep -x hermes
cat /proc/1/cgroup | head -5
which hermes
systemctl --user status hermes-gateway 2>/dev/null
```

## Container → Host Migration

### 1. Verify data persistence

Docker typically bind-mounts the Hermes home:
```bash
ls ~/.hermes/config.yaml       # should exist
ls ~/.hermes/cron/jobs.json     # cron jobs
ls ~/.hermes/scripts/            # helper scripts
```

### 2. Set up systemd user services

Create services for the gateway and dashboard:

```bash
mkdir -p ~/.config/systemd/user

# Gateway service
cat > ~/.config/systemd/user/hermes-gateway.service << 'UNIT'
[Unit]
Description=Hermes Agent Gateway
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=%h/.local/bin/hermes gateway run
Restart=always
RestartSec=5
Environment=HERMES_HOME=%h/.hermes

[Install]
WantedBy=default.target
UNIT

# Dashboard service
cat > ~/.config/systemd/user/hermes-dashboard.service << 'UNIT'
[Unit]
Description=Hermes Agent Dashboard
After=network-online.target hermes-gateway.service
Wants=hermes-gateway.service

[Service]
Type=simple
ExecStart=%h/.local/bin/hermes dashboard --host 127.0.0.1 --port 9119 --no-open
Restart=always
RestartSec=5
Environment=HERMES_HOME=%h/.hermes

[Install]
WantedBy=default.target
UNIT

systemctl --user daemon-reload
systemctl --user enable --now hermes-gateway hermes-dashboard
```

### 3. Migrate cron jobs

Cron jobs often hardcode container paths in both `workdir` and `prompt` fields.

**Scan all jobs for stale paths:**
```bash
cat ~/.hermes/cron/jobs.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
container_paths = ['/home/hermeswebui', '/workspace', '/opt/data', '172.19.0.1']
for j in data['jobs']:
    prompt = j.get('prompt') or ''
    pwd = j.get('workdir') or ''
    found = [cp for cp in container_paths if cp in prompt or cp in pwd]
    if found:
        print(f'{j[\"name\"]}: {found}')
"
```

**Apply fixes via Python** (bulk-edit jobs.json):
```python
import json
with open(os.path.expanduser('~/.hermes/cron/jobs.json')) as f:
    data = json.load(f)

fixes = [
    ('/home/hermeswebui/.hermes/hermes-web-computer', os.path.expanduser('~/repos/hermes-web-computer')),
    ('/home/hermeswebui/.hermes', os.path.expanduser('~/.hermes')),
    ('/workspace/MEMORY.md', os.path.expanduser('~/.hermes/memories/MEMORY.md')),
    ('/workspace/SOUL.md', os.path.expanduser('~/.hermes/SOUL.md')),
    ('/workspace/USER.md', os.path.expanduser('~/.hermes/memories/USER.md')),
    ('/workspace/seans-reporepo', os.path.expanduser('~/repos/seans-reporepo')),
    ('/workspace/qa-reports/', os.path.expanduser('~/.hermes/workspace/qa-reports/')),
    ('172.19.0.1', 'localhost'),
]

for j in data['jobs']:
    # Fix workdir
    wd = j.get('workdir')
    if wd:
        for old, new in fixes:
            wd = wd.replace(old, new)
        if wd == '' or wd == '/workspace':
            wd = None
        j['workdir'] = wd
    # Fix prompt
    prompt = j.get('prompt') or ''
    for old, new in fixes:
        prompt = prompt.replace(old, new)
    # Fix container-centric context lines
    prompt = prompt.replace(
        'You run inside the Hermes container with workspace at /workspace.',
        'You are running on the host.'
    )
    prompt = prompt.replace(
        'You are a proactive maintenance agent running inside the Hermes WebUI Docker container.',
        'You are a proactive maintenance agent running on the host.'
    )
    prompt = prompt.replace(
        'Host repos (at /home/sc/repos/ on the host, not accessible from container)',
        'Local repos at /home/sc/repos/'
    )
    j['prompt'] = prompt

with open(os.path.expanduser('~/.hermes/cron/jobs.json'), 'w') as f:
    json.dump(data, f, indent=2)
```

### 4. Migrate scripts

Check `~/.hermes/scripts/` for stale container references:
```bash
grep -rnl 'hermeswebui\|/workspace\|172\.19\.0\.1\|/opt/data' ~/.hermes/scripts/ | grep -v '.pyc'
```

Common files that need fixing:
- `hermes-backup.sh` — container path detection logic
- `skill-selector-prep.py` — SSH-to-host pattern → direct git operations
- `hwc-visual-qa.sh` — Docker gateway IP → localhost

### 5. Configure SSH for companion containers

If containers (like `hermes-webui`) need to SSH to the host:

```bash
# Install and start SSH server
sudo apt-get install -y openssh-server
sudo systemctl start sshd

# Add container's public key to host user's authorized_keys
mkdir -p ~/.ssh && chmod 700 ~/.ssh
cat /path/to/container/id_ed25519.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Test — container reaches host via Docker gateway IP
docker exec <container> ssh -i <key> -o StrictHostKeyChecking=no <host-user>@<gateway-ip> "echo ok"
```

**Gotcha**: The username in the SSH command MUST match the actual host user. Container setups often hardcode a username (e.g., `sean`) that doesn't exist on the new host. Check `/etc/passwd` for the correct user.

### 6. Update webui settings (if used)

The webui container (`hermes-webui`) keeps settings in:
```bash
# Inside the webui container, settings live at the mounted path:
~/.hermes/webui/settings.json
# The container mounts ~/.hermes → /home/hermeswebui/.hermes
```

Key setting to check: `default_workspace` — should point to a valid path.

## Rollback (if needed)

```bash
systemctl --user stop hermes-gateway hermes-dashboard
docker start hermes
```

## Verification

- [ ] Gateway running: `systemctl --user status hermes-gateway`
- [ ] Dashboard running: `curl http://localhost:9119/`
- [ ] No stale container paths in cron jobs: `grep -c 'hermeswebui\|172.19' ~/.hermes/cron/jobs.json`
- [ ] Cron tick passes: `hermes cron tick --accept-hooks`
- [ ] Scripts compile: syntax-check Python and shell scripts

## Pitfalls

- **User mismatch**: SSH will silently reject keys if the target user doesn't exist. Always verify with `id <username>` on the host.
- **Security scanner blocks SSH**: The Hermes gateway's security scanner flags `ssh` commands. Set `approvals.cron_mode: auto_approve` in config.yaml if cron jobs legitimately need SSH.
- **SSH not available yet? Use the Hermes gateway API dispatch pattern** — when a companion container needs to run a command on the host but SSH isn't configured, the host's Hermes gateway `/v1/chat/completions` endpoint can be used with the `API_SERVER_KEY` from `.env`. See `references/gateway-api-dispatch.md` for the full pattern and caveats.
- **`/workspace` false positives**: Some path replacements leave legitimate `.hermes/workspace/` paths that contain `/workspace` as a substring — distinguish between container-only paths and valid host paths.
- **Multi-line prompts**: Some prompts embed `/workspace` in prose (e.g., "This is writable from this container"). Fix the prose too.
- **systemctl --user not working**: Requires `loginctl enable-linger` for the user to survive logout.
- **Scripts using SSH**: If a script used SSH-to-host (e.g., `skill-selector-prep.py`), rewrite it to run directly now that we're on the host — git clone with `https://` instead of SSH, no rsync needed.
