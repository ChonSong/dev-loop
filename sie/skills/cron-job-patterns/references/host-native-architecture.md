# Host-Native Architecture (as of 2026-06-15)

## Current Environment

| Property | Value |
|----------|-------|
| Host | sc-VirtualBox (Ubuntu 20.04) |
| User | sc |
| Hermes version | 0.16.0 (venv at ~/.hermes/hermes-agent/venv/) |
| Gateway port | 8642 (systemd --user) |
| Dashboard port | 9119 (systemd --user) |
| Python | 3.11.15 (system), pip→3.8 (mismatch — use uv or venv) |
| Node | 20.20.0 at ~/node-v20.20.0-linux-x64/ |
| Go | 1.26 at ~/go/ |
| Docker | Available natively |

## What Changed (June 15)

The system was previously running inside a Docker/Singularity container layer with `network_mode: host`. This meant:
- All host commands required `ssh -i /home/hermes/.ssh/id_ed25519 sean@localhost`
- Repo paths were unreachable without SSH
- Docker gateway IP 172.19.0.1 was needed for service health checks
- Skills carried "SSH Fallback" sections for when SSH failed

**As of June 15, we run directly on the host.** SSH is no longer needed. All terminal() commands execute locally. All paths (`/home/sc/repos/...`) are accessible directly. Localhost is the canonical address for all services.

## Services (systemd --user)

| Service | Port | Path |
|---------|------|------|
| GTO Wizard (Next.js) | 3000 | ~/repos/gto-wizard-clone/apps/web |
| GTO Wizard (FastAPI) | 8001 | ~/repos/gto-wizard-clone/apps/api |
| Hermes Gateway | 8642 | ~/.hermes/hermes-agent |
| Hermes Dashboard | 9119 | ~/.hermes/hermes-agent |
| HWC (Go + Svelte 5) | 3005 | ~/repos/hermes-web-computer/backend |
| energy-aware-task-router | (varies) | ~/repos/energy-aware-task-router |

## Container Services (Docker)

| Container | Ports |
|-----------|-------|
| gto-wizard-clone-postgres-1 | 5432 |
| gto-wizard-clone-redis-1 | 6379 |
| netdata | 19999 |
| starcraft-vnc | 5901, 6080 |

## Dev Loop Architecture

- **player-development-loop** (hourly at :00): Reads master checkpoint, selects project, implements one task, tests, commits
- **coach-development-loop** (hourly at :05): Reviews player commits, runs tests, decides APPROVE/FIX/REVERT
- Both run on `deepseek-v4-flash` (player) / `openrouter/owl-alpha` (coach)
- Both use direct commands — no SSH wrappers
- Checkpoints at ~/.hermes/master-checkpoint.json and per-project .checkpoint.json

## Path Convention

All persistent data and repos live under `/home/sc/`:
- `/home/sc/.hermes/` — Hermes agent state, config, cron, skills, memories
- `/home/sc/repos/` — all project repositories (gto-wizard-clone, hermes-web-computer, etc.)
- `/home/sc/.config/systemd/user/` — systemd service unit files
- `/home/sc/.ssh/` — SSH keys (access to GitHub, not needed for host)
