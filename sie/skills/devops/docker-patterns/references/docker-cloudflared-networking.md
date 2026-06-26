# Docker Container Networking — Key Learnings from hermes-webui Cloudflare Tunnel Setup

## Distroless cloudflared Docker Image — ENTRYPOINT/CMD Conflict

The `cloudflare/cloudflared` Docker image has:
- `ENTRYPOINT: ["cloudflared", "--no-autoupdate"]`
- `CMD: ["version"]`

Running `docker run cloudflared tunnel run <name>` — the extra args go to `ENTRYPOINT` as flags, not to `CMD`. The `["version"]` CMD runs first (and exits), preventing `tunnel run` from executing. You cannot override this behavior to make it run `tunnel run` as the entrypoint.

Workaround: run cloudflared as a **host binary** instead of in a Docker container.

## Docker Container + cloudflared — network_mode Pitfalls

### `network_mode: hermes-webui_default` (bridge, same network as target)

```
docker run --network hermes-webui_default cloudflared tunnel run <name>
```
Fails because the extra args (`tunnel run <name>`) go to the ENTRYPOINT, not CMD. The container runs `["cloudflared", "--no-autoupdate", "tunnel", "run", "<name>"]` — the `--no-autoupdate` flag is already baked into the ENTRYPOINT, but the `tunnel run` command still doesn't execute because the CMD `["version"]` runs instead and exits.

**Verdict: Does not work.**

### `network_mode: host`

```bash
docker run --network host cloudflared tunnel run --url http://localhost:8787 <name>
```

Cloudflared runs in host network namespace, but:
- hermes-webui container binds to `127.0.0.1:8787` (not `0.0.0.0:8787`)
- Host's `localhost:8787` maps to the host, not the container
- The container's published `127.0.0.1:8787` is only reachable from the **host's** localhost, not from another container's host namespace

**Verdict: Does not work for localhost-only published ports.**

## Correct Approach: Host Binary + Docker Bridge IP

Since Docker container approach fails, run cloudflared as a **host binary**:

1. Download to a persistent location (NOT `/tmp/` — tmpfs wipes on reboot):
   ```bash
   curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
     -o ~/.local/bin/cloudflared
   chmod +x ~/.local/bin/cloudflared
   ```

2. Get the container's IP on the Docker bridge network:
   ```bash
   docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' hermes-webui-hermes-webui-1
   # e.g., 172.19.0.2
   ```

3. Run cloudflared on host with direct bridge IP:
   ```bash
   ~/.local/bin/cloudflared --no-autoupdate \
     --credentials-file /opt/data/cloudflared/hermes-webui-creds.json \
     tunnel run --url http://172.19.0.2:8787 hermes-webui
   ```

## cloudflared v2026.5.0 CLI Syntax

- `tunnel run <name>` must be the **last positional argument** — flags after it are silently ignored
- `--tunnel <name>` as a flag does not exist; use positional form
- `--credentials-file` and `--url` are valid flags that go before the positional `tunnel run`
- Working pattern: `cloudflared [global flags] tunnel run [flags] <tunnel_name>`

## Watchdog for Persistence (when systemctl --user unavailable)

When running in an agent environment without DBUS session bus (can't use `systemctl --user`), use a watchdog script invoked from cron:

```bash
#!/bin/bash
# /opt/data/scripts/hermes-webui-tunnel-watchdog.sh
LOG=/opt/data/logs/hermes-webui-tunnel.log
CRED=/opt/data/cloudflared/hermes-webui-creds.json
TUNNEL_NAME=hermes-webui
TARGET=http://172.19.0.2:8787
BIN=/tmp/cloudflared  # or ~/.local/bin/cloudflared

if pgrep -f "cloudflared.*$TUNNEL_NAME" > /dev/null; then
  echo "[$(date)] OK" >> "$LOG"
else
  echo "[$(date)] Restarting..." >> "$LOG"
  nohup $BIN --no-autoupdate --credentials-file $CRED tunnel run --url $TARGET $TUNNEL_NAME >> "$LOG" 2>&1 &
fi
```

Crontab: `*/5 * * * * /opt/data/scripts/hermes-webui-tunnel-watchdog.sh`

## Key IP Addresses (hermes-webui stack)

| Container | Docker Network | IP |
|-----------|---------------|-----|
| hermes-webui | hermes-webui_default | 172.19.0.2 |
| agent-os | agent-os_agent-net | 172.18.0.2 |

The two stacks are isolated — cloudflared running on host must target the container's bridge IP directly, not via `localhost` (since `localhost` on the host resolves to the host, not the container when the port is bound to `127.0.0.1`).