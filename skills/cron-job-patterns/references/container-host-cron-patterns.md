# Container-Host Cron Patterns — Detail

## SSH Key and Container Identity

- SSH key: `/home/hermeswebui/.hermes/container_key`
- Host IP: `172.19.0.1` (custom Docker network) or `172.17.0.1` (default bridge)
- Host user: `sean`
- Container cron DB: `/home/hermeswebui/.hermes/cron/jobs.json`

## Path Mapping

| Container Path | Host Path | Persistent? |
|---|---|---|
| `/home/hermeswebui/.hermes/hermes-web-computer` | `/home/sean/.hermes/hermes-web-computer` | Yes (synced via hermes-sync) |
| `/opt/data/hermes-web-computer` | `/home/sean/.hermes/hermes-web-computer` | Yes (symlinked or bind-mounted) |
| `/workspace/gto-wizard-clone` | N/A (container-only workspace) | Yes, when `/workspace` volume is mounted |
| `/tmp/gto-wizard-clone` | N/A | NO — tmpfs, wiped on restart |
| `/workspace/` | Various | Only present in containers with workspace volume mounted. Auto-continue cron containers may lack it — scan `/opt/data/` as fallback. |

## Known Service Ports

| Service | Host Port | Container Reachable? |
|---|---|---|
| HWC server (agent-os) | 3005 | Yes — `curl 172.19.0.1:3005` |
| HWC legacy tunnel | 3113 | Yes |
| Hermes WebUI | 8787 | Yes (self) |
| agent-os-backend | 3001 | Yes (internal) |
| webhook-emitter | - | Runs as systemd service |

## Cron Job Fix Checklist

When a cron job fails repeatedly:
1. Check `last_error` in `cron/jobs.json` — is it a path issue, connection error, or rate limit?
2. Check `workdir` — is it `/tmp`? Switch to `/workspace`
3. Check `deliver` — is it `origin` with `null` origin? Switch to `local`
4. Check paths in prompt — do they match container paths, not host paths?
5. Check if target service is running — `curl` to host IP from container
6. If service is down, SSH to host and restart

## Jobs Fixed in This Session

| Job ID | Name | Fix Applied |
|---|---|---|
| `4d2609ce31ba` | HWC canary | Re-enabled, deliver→local, added host process check |
| `ecb3846b907b` | HWC rebuild | Re-enabled, deliver→local, simplified to file/git checks only |
| `4285b8696203` | HWC nightly | Re-enabled, deliver→local, added workdir, removed Go build steps |
| `5521adb0ed74` | GTO Phase 2 | workdir /tmp → /workspace, added .env fallback |
| `70eabe13c2e2` | GTO Phase 4+5+6 | workdir /tmp → /workspace, deliver→local |
