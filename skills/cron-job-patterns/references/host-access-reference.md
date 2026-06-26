# Host Access Reference — Container → Host

⚠️ **This file was written 2026-06-03 and partially stale.** SSH access is currently BROKEN (see `references/ssh-broken-2026-08.md`). Go is installed but NOT on PATH (see §4 of the main SKILL.md for the explicit toolchain path). For current SSH key locations, see `references/ssh-key-troubleshooting.md`.

## SSH Access (HISTORICAL — no longer works)

**Previously working configuration (as of 2026-06-03):**
```bash
ssh -i /home/hermes/.ssh/id_ed25519 -o ConnectTimeout=10 -o StrictHostKeyChecking=no sean@localhost "<command>"
```

- Key: `/home/hermes/.ssh/id_ed25519` (ed25519, agent-forwarded, no password) — **does not exist in current container**
- User: `sean`
- Host: `localhost` (container has `network_mode: host`) — **connection refused on port 22**

**Current status:** SSH to host from container is broken. No key path is guaranteed to work. If you need host-level operations, try these paths (in order):
1. `ssh host` — if `~/.ssh/config` exists with `Host host` alias
2. `ssh -i /home/hermeswebui/.ssh/id_ed25519 sean@172.19.0.1 "echo ok"` — the most likely working key
3. Redesign the job to run entirely from the container (see `references/ssh-broken-2026-08.md`)

## Host Service Endpoints

| Service | Host Port | Health Check | Notes |
|---------|-----------|-------------|-------|
| HWC (hermes-web-computer) | 3005 | `curl -s --connect-timeout 5 http://172.19.0.1:3005/` → expect 200 | Go backend |
| GTO Wizard Clone (web) | 8564 | `curl -s --connect-timeout 5 http://172.19.0.1:8564/` → expect 200 | Next.js |
| GTO Wizard Clone (api) | 8003 | `curl -s --connect-timeout 5 http://172.19.0.1:8003/` → expect 200 | FastAPI |
| Hermes WebUI | 8787 | Via Cloudflare tunnel | Docker container `hermes` |
| Streamlit (onetag) | 8501 | Via Cloudflare tunnel only | Auth wrapper on 8501, internal on 8502 |

## Network Mode Quirks

- Container uses `network_mode: host` BUT `localhost` still resolves to container loopback
- To reach host services: use Docker bridge `172.19.0.1` directly (curl) or try SSH
- `curl http://localhost:3005` from container may or may not reach host depending on service binding
- Always test with `--connect-timeout 5` first; if connection refused, try `172.19.0.1`
- When terminal is blocked (cron mode), `browser_navigate` can substitute for curl as a port-check fallback — see SKILL.md §3. `web_extract` blocks private/internal addresses, so it cannot be used for host checks.

## Go Toolchain

Go IS installed but NOT on PATH. The exact binary:
```
/home/hermeswebui/.hermes/home/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.26.0.linux-amd64/bin/go
```
See `cron-job-patterns` SKILL.md §4 for full build instructions.

## Read-Only Paths

| Path | Writable? | Notes |
|------|-----------|-------|
| `/opt/data/home/.hermes/memories/` | ✅ Yes | Active memory store |
| `/opt/data/hermes-sync/` | ❌ No | Bind-mounted RO from host |
| `/opt/data/` (most dirs) | ✅ Yes | Persistent data |
| `/tmp/` | ⚠️ tmpfs | Wiped on container restart |
| `/workspace/` | ✅ Yes | Persistent project dirs |

## Known Repo Locations

| Repo | Path | Notes |
|------|------|-------|
| HWC (hermes-web-computer) | `/home/hermeswebui/.hermes/hermes-web-computer` | Go + Svelte |
| GTO Wizard Clone | `/home/hermeswebui/gto-wizard-clone` | Python + Next.js |
