# Container-to-Host Cron Audit — Session 2026-06-14

## Context
Hermes was migrated from Docker container to host via systemd on 2026-06-13.
This session (2026-06-14) audited and fixed all cron jobs + scripts with stale container-only paths.

## Path Mapping (Applied)

| Container pattern | Host replacement |
|---|---|
| `/home/hermeswebui/.hermes` | `/home/sc/.hermes` |
| `/home/hermeswebui/.hermes/hermes-web-computer` | `/home/sc/repos/hermes-web-computer` |
| `/workspace/MEMORY.md` | `/home/sc/.hermes/memories/MEMORY.md` |
| `/workspace/SOUL.md` | `/home/sc/.hermes/SOUL.md` |
| `/workspace/USER.md` | `/home/sc/.hermes/memories/USER.md` |
| `/workspace/seans-reporepo` | `/home/sc/repos/seans-reporepo` |
| `/workspace/qa-reports/` | `/home/sc/.hermes/workspace/qa-reports/` |
| `/workspace/` (generic) | `/home/sc/repos/` (check each case) |
| `/opt/data` | `/home/sc/.hermes` |
| `172.19.0.1` (Docker gateway IP) | `localhost` |
| `/home/hermeswebui/.hermes/container_key` | No longer needed — on host directly |
| `ssh -i /path/key user@172.19.0.1 "cmd"` | `systemctl --user cmd` or direct command |

## Text Replacements (Prompt Context Lines)

- "You run inside the Hermes container with workspace at /workspace." → "You are running on the host. All paths are host-native."
- "You run in an isolated container. /workspace/ may not exist." → "You are running on the host. Use /tmp/ for temporary files."
- "You are a proactive maintenance agent running inside the Hermes WebUI Docker container." → "You are a proactive maintenance agent running on the host."
- "Host repos (at /home/sc/repos/ on the host, not accessible from container)" → "Local repos at /home/sc/repos/"
- "- /workspace/ IS writable from this container." → "- All paths are writable (running on host)."

## Script Fixes

### hermes-backup.sh
Replace container auto-detection block:
```bash
# OLD
if [ -z "$HERMES_HOME" ]; then
    if [ -d /home/hermeswebui/.hermes ]; then
        export HERMES_HOME=/home/hermeswebui/.hermes
    else
        export HERMES_HOME=/opt/data
    fi
fi

# NEW
if [ -z "$HERMES_HOME" ]; then
    export HERMES_HOME="$HOME/.hermes"
fi
```

### skill-selector-prep.py
Full rewrite needed — the old script used SSH to reach host, cloned repos on host, rsynced into container. On host:
- Replace `SSH_BASE` / `SCP_BASE` with direct git clone/pull to `/tmp/`
- Replace all `/home/hermeswebui/.hermes` paths with `Path.home() / ".hermes"`
- Replace all `/workspace/` paths with `Path.home() / "repos" / <name>`
- CACHE_DIR → `$HOME/.hermes/skill-selector-cache/`

## Verification Checklist

After all edits:
1. `bash -n <script>.sh` — shell syntax check
2. `python3 -c "import ast; ast.parse(open('<script>').read())"` — Python syntax check
3. `hermes cron tick --accept-hooks` — reload scheduler
4. `hermes cron list | grep workdir` — verify no stale workdirs remain
5. Bulk scan: `cat ~/.hermes/cron/jobs.json | python3 -c "..."` checking for `hermeswebui`, `/workspace`, `172.19`, `/opt/data`
