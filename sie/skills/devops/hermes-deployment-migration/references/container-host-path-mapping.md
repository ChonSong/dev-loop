# Container → Host Path Mapping (session example)

Exact mappings applied when migrating Hermes from Docker container to native host.

## Cron Jobs Fixed (9 jobs, 18 changes)

| Job ID | Name | Type of Fix |
|--------|------|-------------|
| `0175050d9c29` | Memory Curation | Prompt: `/workspace/MEMORY.md` → `~/.hermes/memories/MEMORY.md`, removed container context |
| `ad90af79146c` | Hermes Full Backup | Workdir + prompt: `/home/hermeswebui/.hermes` → `~/.hermes` |
| `e4d95660ab35` | seans-reporepo refresh | Prompt: `/workspace/seans-reporepo` → `~/repos/seans-reporepo` |
| `64280d3687bf` | context-budget-audit | Prompt: `/home/hermeswebui/.hermes/skills` → `~/.hermes/skills` |
| `4d2609ce31ba` | HWC canary watch | Prompt: `172.19.0.1` → `localhost`, SSH → direct systemctl |
| `ecb3846b907b` | HWC rebuild + deploy | Workdir + prompt: container paths → `~/repos/hermes-web-computer` |
| `4285b8696203` | HWC nightly build | Workdir + prompt: container paths → `~/repos/hermes-web-computer` |
| `65520f7d71f9` | skill-selector-prep | Prompt: `/home/hermeswebui/.hermes` → `~/.hermes` |
| `e8f57eddfa43` | Daily QA Audit | Prompt: `/workspace/qa-reports/` → `~/.hermes/workspace/qa-reports/` |
| `1a8cbe1ed293` | auto-continue-work | Workdir `/workspace` cleared, prompt converted to host context |

## Path Mappings

| Pattern | Replacement |
|---------|-------------|
| `/home/hermeswebui/.hermes/hermes-web-computer` | `~/repos/hermes-web-computer` |
| `/home/hermeswebui/.hermes` | `~/.hermes` |
| `/workspace/MEMORY.md` | `~/.hermes/memories/MEMORY.md` |
| `/workspace/SOUL.md` | `~/.hermes/SOUL.md` |
| `/workspace/USER.md` | `~/.hermes/memories/USER.md` |
| `/workspace/seans-reporepo` | `~/repos/seans-reporepo` |
| `/workspace/qa-reports/` | `~/.hermes/workspace/qa-reports/` |
| `172.19.0.1` (Docker gateway) | `localhost` |
| `ssh -i <key> sean@<host>` | Direct command (no SSH needed on host) |

## Scripts Fixed

| Script | Fix |
|--------|-----|
| `hermes-backup.sh` | Replaced container auto-detection with `$HOME/.hermes` |
| `skill-selector-prep.py` | Rewrote SSH-to-host → direct git clone/pull with `https://` URLs |
| `hwc-visual-qa.sh` | (Noted but not critical — not called by any cron job) |

## SSH Key Setup

The webui container had an SSH key at `~/.hermes/home/.ssh/id_ed25519` (mounted from container path `/home/hermeswebui/.hermes/home/.ssh/id_ed25519`).

**Problem**: No SSH server on host, wrong username in SSH commands (`sean` → `sc`).

**Fix**:
```bash
sudo apt-get install -y openssh-server
sudo systemctl start sshd
cat ~/.hermes/home/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys
# Verify: docker exec hermes-webui-hermes-webui-1 \
#   ssh -i /home/hermeswebui/.hermes/home/.ssh/id_ed25519 \
#   -o StrictHostKeyChecking=no sc@172.19.0.1 "echo ok"
```

## Verification Commands

```bash
# Check all cron jobs for remaining stale paths
cat ~/.hermes/cron/jobs.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
container = ['/home/hermeswebui', '/workspace', '/opt/data', '172.19.0.1', 'docker gateway', 'container_key']
for j in data['jobs']:
    prompt = j.get('prompt') or ''
    pwd = j.get('workdir') or ''
    found = [cp for cp in container if cp in prompt and '.hermes/workspace' not in prompt or cp in pwd]
    if found:
        print(f'{j[\"name\"]}: {found}')
print('Done')
"

# Check scripts for stale refs
grep -rnl 'hermeswebui\|/workspace\|172\.19\.0\.1\|/opt/data' ~/.hermes/scripts/

# Verify active services
systemctl --user status hermes-gateway --no-pager | head -3
systemctl --user status hermes-dashboard --no-pager | head -3
hermes cron list | grep Workdir
