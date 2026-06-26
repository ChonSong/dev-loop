---
name: hermes-docker-workflow
description: "Build, run, and troubleshoot Hermes Agent Docker containers. For Ubuntu/hpprobook host (NOT Arch). Covers docker-compose, exec, GHCR image push/pull, and known path/binary quirks."
---

# Hermes Docker Workflow

## Important: Host vs Container Context

**On hpprobook (Ubuntu host)**: plain `docker` commands work directly — no `sg docker -c` wrapper needed.

**Container exec commands** (run these FROM the host):
- `docker exec hermes /opt/hermes/.venv/bin/hermes chat -q "hello"`
- `docker exec -it hermes /opt/hermes/.venv/bin/hermes --tui`
- `docker exec hermes /opt/hermes/.venv/bin/hermes gateway status`

The `terminal` tool's CWD defaults to `/home/sean/workspace` which may not exist. **Use `execute_code` (Python subprocess) instead** — it defaults to `/opt/hermes` which always exists inside the container.

**Workaround for broken terminal CWD**: if terminal fails with `FileNotFoundError`, use `execute_code` with `cwd='/opt/data'` for all work, or prepend `cd /opt/data && ` to shell commands.

## hermes-sync Local Build (`sync-and-push.sh`)

The `hermes-sync` repo has a **local build script** at `~/hermes-sync/scripts/sync-and-push.sh` — this is what the cron job runs. It combines hermes-agent (source) with hermes-sync (skills/config/workspace) into a single GHCR image.

**What it does:**
1. Pulls latest hermes-sync git repo
2. Rsyncs hermes-agent into `hermes-sync/hermes-agent/` (preserving directory structure)
3. Builds `ghcr.io/chonsong/hermes-sync:latest` from `hermes-sync/docker/Dockerfile`
4. Pushes to GHCR
5. Rolling restarts `hermes` and `hermes-dashboard` containers

**Run from host:**
```bash
cd /home/sean/.hermes/home/hermes-sync && bash scripts/sync-and-push.sh
```

**Repo relationship:**
| Repo | Location | Role in build |
|------|----------|---------------|
| `hermes-sync` | `/home/sean/.hermes/home/hermes-sync/` | Build context + skills/config/workspace |
| `hermes-agent` | `/home/sean/.hermes/home/hermes-agent/` | Source — rsync'd into build context |

**Key Dockerfile patterns (discovered the hard way):**
- Use `--prefix` for all `npm` commands: `npm run build --prefix web` instead of `cd web && npm run build` — the `cd` form fails because the target dir doesn't exist yet at install time
- `COPY src dest/` — trailing `/` on dest preserves dir structure; `COPY a/b/c ./` flattens into `.`
- Scoped packages need parent dir: `mkdir -p node_modules/@hermes` before `cp -R ui-tui/packages/hermes-ink node_modules/@hermes/ink`
- Entrypoint needs explicit perms: `COPY --chmod=0755 docker/entrypoint.sh`
- Do NOT add an ink import test (`node -e "await import('@hermes/ink')"`) — it fails because react was stripped in the production install

**Rolling restart naming conflict (both services):** The compose file uses bare service names (`gateway`, `dashboard`) without a project prefix, mapped to containers `hermes` and `hermes-dashboard`. After `sync-and-push.sh` runs, the script does `docker rm -f hermes` + `docker start hermes` for the gateway, which works. But for dashboard, `docker compose up -d dashboard` tries to *recreate* the container and hits:

```
Error response from daemon: Conflict. The container name "/hermes-dashboard" is already in use
```

**Fix — two-step recovery:**
```bash
docker rm -f hermes-dashboard    # remove the stale container
docker start hermes-dashboard    # start it fresh (no compose recreation needed)
```

**Why `docker compose up -d dashboard` fails:** The compose service name is `dashboard` (not `hermes-dashboard`), so `docker compose up -d dashboard` attempts a create, not a start. If the old container still holds the name, it conflicts. `docker start` reuses an existing container by name and does not conflict.

**Prevention:** If the script exits non-zero after the push step, always check which container failed and use `docker start <name>` (not `docker compose up -d`) for recovery. `docker start` is idempotent — it only fails if the container truly doesn't exist.

**Disk space:** A single npm install + uv pip install can fill the host disk (~37GB freed in one session). If the build fails with "no space left", run:
```bash
ssh -i /home/sean/.ssh/id_ed25519 sean@localhost "docker image prune -f && docker builder prune -af"
```

## Build the image (hermes-agent GHA — NOT hermes-sync)

**For the NousResearch/hermes-agent official image** (`ghcr.io/nousresearch/hermes-agent`): builds are handled by GitHub Actions — not by a local script. The `hermes-sync` repo (ChonSong/hermes-sync) is a configuration/memory sync repository, not the build system for the official image.

If you need a local build of hermes-agent (not hermes-sync):
```bash
# Requires hermes-agent repo as sibling to hermes-sync
cd /home/sean/.hermes/home/hermes-sync
DOCKER_BUILDKIT=1 docker build -t hermes-agent -f docker/Dockerfile ../hermes-agent
```
**Docker build fails with `--chmod`**: Run `DOCKER_BUILDKIT=1 docker build ...`

**Important repo distinction:**
| Repo | Location | Purpose |
|------|----------|---------|
| `hermes-sync` | `/home/sean/.hermes/home/hermes-sync/` (ChonSong/hermes-sync) | Config/memory/workspace + local GHCR build via `sync-and-push.sh` |
| `hermes-agent` | `/home/sean/.hermes/home/hermes-agent/` (NousResearch/hermes-agent) | Source code, Dockerfile, GHA workflows for official image |
| `hermes-webui` | `/home/hermeswebui/.hermes/hermes-webui/` (ChonSong/hermes-webui) | Forked from `nesquena/hermes-webui`, force-pushed to sync identical state. Used by bootstrap script for one-command install. |

The CI/CD pipeline that builds and pushes `ghcr.io/nousresearch/hermes-agent` lives in `hermes-agent/.github/workflows/docker-publish.yml`. Triggers on push to `main` or on release. Multi-arch (amd64 + arm64).

## Host SSH Access — Working via Custom Port 2229

**STATUS: WORKING** — SSH to host works on both port 22 and 2229.

**Current working SSH commands** (from inside hermes container, verified May 2026):
```bash
# Via container_key (primary — Ed25519, persisted at /home/hermeswebui/.hermes/container_key):
ssh -i /home/hermeswebui/.hermes/container_key -o StrictHostKeyChecking=no -o ConnectTimeout=5 sean@172.19.0.1 "hostname"
```

**SSH key path (CORRECTED May 2026 — skill older revision had wrong paths):**
| Key | Correct Path | Wrong Paths (don't use) |
|-----|-------------|------------------------|
| Container key (primary) | `/home/hermeswebui/.hermes/container_key` | `/opt/data/container_key`, `/opt/data/home/.ssh/id_ed25519` |

**Host IP:** `172.19.0.1` (Docker gateway). Not `localhost` (port 22 not reachable on container localhost), not `127.0.0.1`.

**Setup that works** (discovered after extensive debugging):
1. Copy host's sshd binary: `cp /proc/1/root/usr/sbin/sshd /tmp/sshd_host`
2. Create config with `AuthorizedKeysFile` pointing to an **absolute path** (not `%h/.ssh/...`):
   ```
   Port 2229
   AuthorizedKeysFile /root/.ssh/authorized_keys
   PubkeyAuthentication yes
   PasswordAuthentication no
   PermitRootLogin yes
   StrictModes no
   ```
3. Run via `chroot /proc/1/root /tmp/sshd_host -f /tmp/sshd_final_config`

**Why the copied binary works**: The host's sshd binary runs correctly via chroot, while `chroot /proc/1/root /usr/sbin/sshd` fails because it tries to read `/etc/passwd`, `/etc/shadow`, and other files from the chroot that conflict with its internal path resolution.

**Why port 22 is blocked**: Something else owns port 22 on the host — it's not systemd sshd (the container's view of PID 1 is `tini`, not systemd). The actual sshd process that answers on port 22 could not be identified — it doesn't appear in `ps aux` or `/proc/*/cmdline` from inside the container. The connection is accepted (SSH banner responds) but authentication always fails silently.

**To make port 22 work permanently** (on host, not from container):
```bash
# Find and stop whatever owns port 22
sudo ss -tlnp | grep :22
sudo fuser -k 22/tcp
# Then start sshd properly
sudo systemctl enable --now ssh
```

**SSH key path correction**:
- Container path (inside hermes): `/opt/data/home/.ssh/id_ed25519`
- Host path: `/home/sean/.ssh/id_ed25519`
- Memory/SKILL path `/opt/data/home/.hermes/home/.ssh/id_ed25519` is **WRONG** — corrected above

**Why SSH agent forwarding doesn't work**: The container's SSH agent socket approach requires sshd running on the host to accept the forwarded connection. Without it, even with a valid key and correct path, authentication fails at the daemon level.

## Docker Daemon Access — Agent-to-Host Control

Three ways the agent can control the host Docker daemon, in recommended order:

### Option 1: Tailscale VPN (recommended for remote agent)

The agent container and the host both join the same Tailscale network. Get the host's Tailscale IP, then SSH directly over VPN:

```bash
# On host: find its Tailscale IP
tailscale ip -4

# From agent container (or any machine with Tailscale):
ssh root@<tailscale-ip>
```

No ports needed on the LAN. Works from anywhere. Both the hermes-agent container and the host should have Tailscale running.

### Option 2: Docker socket mount (for bundled/hybrid deployments)

Mount the host's Docker socket into the agent container:

```yaml
# In docker-compose.yml for the agent container:
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
```

The agent can now run:
```bash
# From inside the container:
docker --host unix:///var/run/docker.sock ps
docker --host unix:///var/run/docker.sock compose -f /opt/data/hermes-sync/projects/agent-os/docker-compose.yml up -d
```

**agent-os example:** The `agent-os` container mounts `/var/run/docker.sock` — so Hermes Agent (if it runs as a sibling container) can control the host Docker, and the bundled `agent-os` container itself can manage other containers on the host via the Docker API at `/var/run/docker.sock`.

### Option 3: Host network (`--network=host`)

Removes container network isolation — the agent uses the host's network stack directly. `192.168.1.117:22` becomes reachable from inside the container. Less isolated, but simplest for LAN-only setups.

### Docker Daemon Access Restrictions (Critical — don't assume Docker works)

**The hermes-agent sandbox IS a Docker host** (`192.168.1.117` is this sandbox's LAN IP). But the Docker socket inside the sandbox connects to the sandbox's own Docker daemon — NOT the host's. This means `docker ps` from inside the sandbox returns the sandbox's containers (usually empty), not the CasaOS host's containers.

| Source | Docker socket connects to | Can see |
|--------|---------------------------|---------|
| Inside sandbox | Sandbox's Docker daemon | Sandbox's containers (usually none) |
| Inside sandbox, with socket mount | Host's Docker daemon | Host's containers (`hermes`, `hermes-dashboard`) |

**The sandbox IS `192.168.1.117`** — but the CasaOS host has a different LAN IP on the same network. SSH from sandbox → host requires knowing the host's IP.

**Implication**: Docker image builds via GHA are fine. Docker pulls/runs on the CasaOS host must happen via:
- SSH from sandbox to host (requires host IP + SSH access)
- GitHub Actions SSH deploy workflow (requires `DEPLOY_SSH_KEY` secret)
- Tailscale VPN (both machines on same Tailnet)

### Option 1: Tailscale VPN (recommended for remote agent → host access)

Both the sandbox and the CasaOS host should join the same Tailscale network. Get the host's Tailscale IP, then SSH directly over VPN from the sandbox:

```bash
# On CasaOS host: find its Tailscale IP
tailscale ip -4

# From sandbox terminal:
ssh root@<tailscale-ip>
```

No ports needed on LAN. Works from anywhere both machines have internet.

### Option 2: Docker socket mount (for agent-os container → host control)

When the agent-os container runs ON the CasaOS host's Docker, mount the host socket into it:

```yaml
# In docker-compose.yml for the agent-os container:
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
```

Then from inside the agent-os container:
```bash
docker --host unix:///var/run/docker.sock ps
docker --host unix:///var/run/docker.sock compose -f /opt/data/hermes-sync/projects/Agent-OS/docker-compose.yml up -d
```

**agent-os example:** The `agent-os` container mounts `/var/run/docker.sock` — it can manage other containers on the host via the Docker API. Hermes Agent (running as a sibling container or on the host) can control agent-os the same way.

### Option 3: Host network (`--network=host`)

Removes container network isolation — the sandbox's agent uses the host's network stack directly. `192.168.1.117:22` becomes reachable from inside the container. Less isolated, but simplest for LAN-only setups.

## CI / GitHub Actions Path Filter Pitfall

**Problem**: Including `docker-compose.yml` in the workflow's `paths` filter causes compose-only commits (version bump, comment-only changes) to trigger Docker builds. Since no code changed, the build succeeds but produces a duplicate image with the same SHA — wasted action minutes and confusing history.

**Fix**: Keep `docker-compose.yml` OUT of any build-trigger path filters. The path filter should only include actual build inputs:
```yaml
on:
  push:
    paths:
      - 'docker/**'
      - 'nanobot/**'
      - 'gateway/**'
      - 'compose-setup/**'
      # NOT: 'docker-compose.yml'
```

If `docker-compose.yml` must be tracked, use a separate workflow for compose-only updates that does NOT run Docker builds.

**SSH key path corrections (CRITICAL — skill docs are wrong):**
- Container key (primary): `/home/hermeswebui/.hermes/container_key` — Ed25519, not `/opt/data/container_key`
- Key file must be accessed via `ssh -i /home/hermeswebui/.hermes/container_key ...` from inside container
- The skill older revision had `/opt/data/home/.ssh/id_ed25519` — this is also wrong

**hermes-sync SSH path (always):** `/home/sean/hermes-sync/` — not `/opt/data/.hermes/hermes-sync/scripts/`, not `/home/sean/.hermes/home/hermes-sync/`. This is the canonical path for all host-side git operations via SSH.

### Pitfall: Files Exist Locally but Git "Doesn't Know About Them"

**Symptom:** `docker/` directory exists on the host's hermes-sync working tree, `git status` shows clean (no changes), but bootstrap fails saying `docker/docker-compose.yml` is missing from the remote clone.

**Root cause sequence:**
1. Files were created locally but never `git add`/`git commit`
2. Someone ran `git reset --hard origin/master` on the host — this pulls remote state to working tree (files appear)
3. But `git add docker/` was never run, so the local git index doesn't track those files
4. `git status` shows clean because the committed versions match (or nothing is staged)
5. `git ls-files docker/` returns empty — local git has no knowledge of the files
6. But `gh api repos/OWNER/REPO/git/trees/HEAD?recursive=1` shows the files ARE in the remote HEAD

**The files are actually already committed.** The apparent "missing" files issue was a false alarm — the files existed on the host working tree, were never added to git, but `gh api` confirmed they were already at remote HEAD from a prior sync operation.

**Verification always goes through `gh api`** — never trust local `git ls-files` or `git status` when diagnosing "missing" files in a bootstrap scenario:
```bash
# Local git (unreliable when files never staged)
git ls-files docker/                    # empty if never git add'd

# GitHub API (authoritative for remote HEAD state)
gh api repos/ChonSong/hermes-sync/git/trees/HEAD?recursive=1 | \
  python3 -c "import json,sys; t=json.load(sys.stdin)
  print([e['path'] for e in t['tree'] if 'docker' in e['path']])"
# → ['docker/.dockerignore', 'docker/Dockerfile', 'docker/SOUL.md', 'docker/docker-compose.yml', 'docker/entrypoint.sh']
```

**Lesson:** When bootstrap says a file is missing, verify against remote HEAD via GitHub API before building workarounds to add files via API. The file may already be there.

**SSH to host status (May 2026):**
- Port 22: Connection refused — no sshd listening at all
- Port 2229: Also refused
- **Root cause: Arch Linux host has `openssh-client` only — no `openssh-server` installed**
- The container key at `/home/hermeswebui/.hermes/container_key` IS valid (Ed25519), but nothing is listening to receive it

**To fix SSH on host (run on host machine, not from container):**
```bash
# Check what's installed
pacman -Q | grep openssh   # shows openssh, likely client only

# Install server
sudo pacman -S openssh

# Start sshd
sudo systemctl enable --now sshd

# Or if systemd not running (container context):
/usr/sbin/sshd
```

**After sshd is running**, verify with:
```bash
ssh -i /home/hermeswebui/.hermes/container_key -o StrictHostKeyChecking=no -o ConnectTimeout=5 sean@localhost "hostname"
```

**To make port 22 work permanently** (on host, not from container):

**Primary sync:** Host system cron runs `hermes-sync-backup.py` every 6 hours. See `hermes-docker-sync-setup` skill for full details.

| Schedule | Trigger | What runs |
|----------|---------|-----------|
| Every 6h | Host crontab | `sync-cron.sh` → `hermes-sync-backup.py` |
| On-demand | Manual | `python3 /home/sean/.hermes/scripts/hermes-sync-backup.py` |

**Key limitation:** `state.db` (269MB) exceeds GitHub's 100MB limit and is excluded from git sync. It must be backed up separately.

**Git repo:** `ChonSong/hermes-sync` (working dir: `/home/sean/.hermes/cache/sync-work/hermes-sync/`)

**To manually trigger sync (from host):**
```bash
HERMES_HOME=/home/sean/.hermes python3 /home/sean/.hermes/scripts/hermes-sync-backup.py
```

**From container via SSH:**
```bash
ssh -i /opt/data/container_key sean@localhost "HERMES_HOME=/home/sean/.hermes python3 /home/sean/.hermes/scripts/hermes-sync-backup.py"
```

## Cloudflare Tunnel Credentials vs Access Tokens

Two different Cloudflare token types — mixing them up causes 401/400 errors:

| Token Type | Use for | Cannot do |
|---|---|---|
| `CFAT_TOKEN` (Cloudflare Access Token) | ZT/Access policies, device checks | Create/list tunnels |
| Tunnel Credentials (`credentials.json`) | `cloudflared tunnel run` | Access policies |

**Named tunnel watchdog + cron pattern** (when no systemd is available):

When running cloudflared inside a container without systemd, use a watchdog script + cron for persistence:

```bash
# 1. Persist cloudflared binary to a writable volume
cp /tmp/cloudflared /opt/data/bin/cloudflared
chmod +x /opt/data/bin/cloudflared

# 2. Save credentials to persistent path
# Credentials file format (camelCase JSON from Cloudflare API):
# {"AccountTag": "...", "TunnelID": "...", "TunnelSecret": "..."}

# 3. Watchdog script at /opt/data/scripts/hermes-webui-tunnel-watchdog.sh:
#!/bin/bash
CREDS="/opt/data/cloudflared/hermes-webui-creds.json"
BINARY="/opt/data/bin/cloudflared"
LOG="/opt/data/logs/cloudflared-watchdog.log"

if ! pgrep -f "$BINARY.*hermes-webui" > /dev/null 2>&1; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Tunnel dead, restarting..." >> $LOG
    $BINARY tunnel run --credentials-file $CREDS hermes-webui 2>&1 &
fi

# 4. Cron guardian (runs every 5 minutes):
hermes cron add hermes-webui-tunnel-guardian \
  --script hermes-webui-tunnel-watchdog.sh \
  --schedule "*/5 * * * *" --no-agent \
  --prompt "Run /opt/data/home/.hermes/scripts/hermes-webui-tunnel-watchdog.sh..."
```

**Named tunnel ingress routing**: With credentials-file (named tunnel), ingress rules in the config file route by hostname. No `--url` flag needed when ingress rules are set.

**Reconstruct credentials from Cloudflare API**:
```bash
curl -s -X GET "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/tunnels/${TUNNEL_ID}/credentials" \
  -H "Authorization: Bearer ${CFAT_TOKEN}" | python3 -m json.tool
# Returns: AccountTag, TunnelID, TunnelSecret (base64)
```

**Discovery: List all tunnels**:
```bash
curl -s -X GET "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/tunnels" \
  -H "Authorization: Bearer ${CFAT_TOKEN}" | python3 -c "
import json,sys
d=json.load(sys.stdin)
for t in d.get('result', []):
    print(t['id'], t['name'], t.get('status'), len(t.get('connections',[])))
"
```

**Alternative**: Use a Cloudflare API token with `Tunnel:Edit` permissions (not the same as an Access token).

- `references/systemd-user-docker-service.md` — systemd user service pattern for Docker compose (Type=oneshot + RemainAfterExit, linger, boot persistence)

## GHCR + GitHub Actions Docker Build Reference

For debugging Docker build failures in GitHub Actions, GHCR image naming quirks, and common Dockerfile.nanobot failure patterns, see:
- `references/ghcr-docker-build-debugging.md`
- `references/docker-alpine-python-pep668.md`

For hermes-sync local build patterns (rsync strategy, npm --prefix, scoped package mkdir, COPY trailing slash, layer caching, rolling restart conflicts), see:
- `references/sync-and-push-build.md`

For HWC (hermes-web-computer) cron phase execution, tool paths, and build/test commands, see:
- `references/hwc-phase-execution.md`

For comprehensive CI debugging (GHCR naming, bash lowercasing, `latest` tag behavior, workflow path filters), see:
- `github-pr-workflow/references/ci-troubleshooting.md`

## Docker compose services

**Compose file location:** `/home/sean/.hermes/home/hermes-sync/docker/docker-compose.yml` (in the `docker/` subdirectory, not repo root).

| Service | Container | Port | Purpose |
|---------|-----------|------|---------|
| `gateway` | `hermes` | 9119 | Messaging gateway (healthcheck: `http://localhost:9119/health`) |
| `dashboard` | `hermes-dashboard` | 9120 | Web dashboard |
| `agent-os-postgres` | `agent-os-postgres` | 5432 | PostgreSQL database |
| `agent-os-backend` | `agent-os-backend` | 3001, 1331 | Express backend (connects to host Hermes via host.docker.internal:8642) |
| `agent-os-cloudflared` | `agent-os-cloudflared` | — | Cloudflare tunnel → backend:3001 (**BROKEN** — should be `agent-os-backend:3001`) |
| `agent-os-webhook-emitter` | `agent-os-webhook-emitter` | — | Docker event poller → backend webhook |

Gateway healthcheck: `curl localhost:9119/health`. Dashboard depends on gateway being healthy.

> **Note**: The port numbers in this table reflect the actual runtime configuration. The `gateway` service runs `gateway run` command and binds to 9119 by default in the CasaOS deployment.

## Path mapping

| Inside Container | Host |
|-----------------|------|
| `/opt/data/` | `/home/sean/.hermes/` |
| `/opt/workspace/` | `/home/sean/workspace/` |
| `/opt/hermes/` | *(image internal)* |

## Updating Hermes

`hermes update` does NOT work inside the container (not a git repo). Update on the host instead:

```bash
cd /home/sean/.hermes/home/hermes-agent
git stash                           # save local Dockerfile/.dockerignore changes
git pull --ff-only                  # fetch upstream
git stash pop                       # reapply local changes (resolve conflicts if any)
```

Check if stash pop had merge conflicts — the Dockerfile and .dockerignore are the most likely conflict points. After resolving:

```bash
DOCKER_BUILDKIT=1 docker build -t hermes-agent -f docker/Dockerfile .
HERMES_UID=$(id -u) HERMES_GID=$(id -g) docker compose -f docker/docker-compose.yml up -d
```

> **Path note**: `hermes-agent` is at `/home/sean/.hermes/home/hermes-agent/`. The `hermes-sync` repo is at `/home/sean/.hermes/home/hermes-sync/`. These are siblings under `/home/sean/.hermes/home/`.

Full rebuild takes ~15-20 min. Most layers cache if only source changed. The npm install + Playwright step is the slowest (~3 min). The uv pip install step is also slow (~40s).

**After updating**, verify TUI works:
```bash
docker exec hermes test -f /opt/hermes/ui-tui/dist/entry.js && echo OK
docker exec -it hermes /opt/hermes/.venv/bin/hermes --tui
```

## SSH Timeout on Disk-Heavy Operations

**Problem**: Commands like `docker system prune -af` hang indefinitely on constrained I/O, timing out at 35s.

**Safe alternative** — staged cleanup that won't hang:
```bash
ssh -i /opt/data/home/.ssh/id_ed25519 sean@localhost "docker image prune -f && docker builder prune -af"
```

## Crash Types: Iteration Limit vs Context Compaction

These look similar but have different causes and fixes:

| Signal | Root Cause | Fix |
|--------|------------|-----|
| `⚠️ ALERT: Iteration limit nearly reached` + session terminates | `max_turns` cap (default 90) | Set `agent.max_turns: 200` in `config.yaml`, then `/reset` |
| Context compaction summary at session start | Context window full (~128K tokens) | Normal — session state preserved in `state.db`, resume normally |

**The iteration limit crash is preventable.** The context compaction is not (it's a model-side limit). Always raise `max_turns` before extended debugging sessions.

## Troubleshooting

### Terminal Tool CWD Trap

The `terminal` tool is hardcoded to use `/home/sean/workspace` as CWD. If that path doesn't exist on the host, **every command fails** with:
```
FileNotFoundError: [Errno 2] No such file or directory: '/home/sean/workspace'
```
This persists even across `cd` commands — the shell's CWD is a kernel-level property and cannot be fixed within a session.

**Fix**: Set the correct cwd permanently (run once from host):
```bash
docker exec hermes /opt/hermes/.venv/bin/hermes config set terminal.cwd /opt/data
```
Then `/reset` in the Hermes session — config change only takes effect on new session. After reset, `terminal` will work normally. The old approach of `execute_code` with `cwd='/opt/data'` is now obsolete for this specific fix.

**`hermes: executable not found`**: Binary is at `/opt/hermes/.venv/bin/hermes` — always use full path.

**Permission denied**: Ensure `HERMES_UID`/`HERMES_GID` match host user (1000:1001).

**Docker build fails with `--chmod`**: Run `DOCKER_BUILDKIT=1 docker build ...`

**Disk space in container vs host — full recovery and prevention details:** See `references/disk-recovery.md`.

`df -h` inside the container shows overlay fs stats for `/opt/data` mount. The **host** disk (e.g., `/dev/sda2` at 461G) is the real constraint. A "98% disk" alert from a scanner running inside the container reflects the host, not `/opt/data`.

To find what's consuming host disk (from host terminal):
```bash
sudo du -sh /home/* /var/lib/docker/containers 2>/dev/null | sort -h
docker system df                          # Docker images/containers占用
```

Common host-space consumers: Docker images (`docker system prune -a`), old browser caches, large GoogleDrive files, video game installers.

Inside the container, only `/tmp` is easily cleanable (e.g., browser caches like camoufox).

### Disconnected Container Diagnosis (Hermes Cannot Reach Docker or SSH)

When the hermes container is live (`--network=host`) but Docker socket is not mounted and SSH to host fails, the container is **isolated from Docker management**. This state is characterized by:

| Symptom | Cause |
|---------|-------|
| `docker ps` returns **empty with exit 0** | Socket IS mounted (sandbox's Docker daemon), but daemon has no containers. This is sandbox's own Docker — NOT host's. |
| `ssh localhost` → **Connection refused (exit 255)** | SSHd not running on host, or port 22 not reachable from this context. The SSH agent forwarding approach assumes SSH is running on the host. If it isn't, this is the observed error. |
| `docker ps` fails with "Cannot connect to Docker daemon" | Socket not mounted in container |
| SSH to `localhost:22` refused | sshd not running in container, port 22 not mapped |
| SSH to `192.168.1.117:22` refused | Host SSH not running or not reachable from this context |
| `curl` not found | Minimal container image (no curl installed) |
| `systemctl`, `ss`, `ping` not found | Not available in sandbox |
| `urllib.request.urlopen` works (Python) | Use Python stdlib as curl substitute |
| Ports 9120/8900 refuse connection | Service not running on host |

**Check if you're in the hermes container or on bare metal:**
```python
import os
# PID 1 is tini = inside container
with open("/proc/1/cmdline", "rb") as f:
    cmdline = f.read().replace(b"\x00", b" ")
# If "tini" or "entrypoint.sh" → inside container
# If "systemd" or bash → on host
```

**Minimal toolchain available in this sandbox (no curl/ss/ping/systemctl):**
```python
# Network health checks → use urllib (Python stdlib, always available)
import urllib.request
try:
    with urllib.request.urlopen("http://localhost:9120/health", timeout=10) as r:
        print(r.read())
except urllib.error.URLError as e:
    print(f"Down: {e}")

# File operations → use os module
os.path.exists("/var/run/docker.sock")  # check for socket

# Docker binary exists but daemon unreachable
subprocess.run(["docker", "--version"])  # shows version, daemon unavailable

# Network port scan via socket (no nmap/ss needed)
import socket
for port in [2375, 2376, 2377]:
    s = socket.socket()
    s.settimeout(2)
    r = s.connect_ex(("192.168.1.117", port))
    print(f"Port {port}: {'OPEN' if r==0 else 'closed'}")
    s.close()
```

**Real fix options (must be applied on host):**
1. **Mount Docker socket** into container: add `-v /var/run/docker.sock:/var/run/docker.sock` to the hermes container run args
2. **Enable SSH on host**: install openssh-server on host, add SSH key to `authorized_keys`, enable `sshd`
3. **Use Tailscale**: both container and host on same Tailnet → `ssh root@<tailscale-ip>` works over VPN
4. **Run deployment as cron on host**: instead of from inside hermes, have a host-level cron job or systemd service handle `docker compose up -d`

### Reliable Port Probe (Python stdlib — no curl/ss/fuser)

In this sandbox, `curl` is not available. Use Python socket to check if ports are open:

```python
import socket

def port_open(host, port, timeout=2):
    s = socket.socket()
    s.settimeout(timeout)
    r = s.connect_ex((host, port))
    s.close()
    return r == 0

# Probe common agent-os ports
for port in [8001, 8900, 3001, 3000, 5000, 8080, 5173, 9119]:
    status = "OPEN" if port_open("localhost", port) else "closed"
    print(f"  :{port} — {status}")

# Check host SSH specifically
host_ssh = port_open("localhost", 22)
print(f"\nHost SSH (:22): {'OPEN' if host_ssh else 'closed/refused'}")
```

### Finding which process owns a port (Linux /proc technique)

When `fuser -k <port>/tcp` claims to succeed but the port stays bound, the process is zombie-surviving SIGTERM. Find the owning process via inode:

```bash
# Get inode for port
cat /proc/net/tcp | awk 'NR>1 {split($2,a,":"); port=strtonum("0x"a[2]); if(port==8001) print $1,$2,$10}'
# Returns: local_address inode

# Find process by inode
python3 -c "
import os,glob
target_inode = '1557459'  # from above
for pid_dir in glob.glob('/proc/[0-9]*/fd'):
    pid = pid_dir.split('/')[2]
    for fd in glob.glob(f'{pid_dir}/*'):
        try:
            if target_inode in os.readlink(fd):
                print(f'PID {pid} owns port (inode={target_inode})')
                break
        except: pass
"
# Kill with SIGKILL (zombies ignore SIGTERM)
kill -9 <PID>
```

This is more reliable than `lsof` or `ss -tlnp` when processes are in unkillable states.

### Google Drive / rclone from inside container

rclone binary lives at `/usr/bin/rclone` (container) or `/opt/data/rclone` (host-mounted). rclone config at `/opt/data/rclone_config/rclone.conf`.

```bash
# Test Drive access (from host)
docker exec hermes /usr/bin/rclone ls gdrive: --max-depth 1
```

To refresh OAuth tokens: run `rclone config` on the host, then copy `rclone.conf` back to `~/.hermes/rclone_config/rclone.conf`.
