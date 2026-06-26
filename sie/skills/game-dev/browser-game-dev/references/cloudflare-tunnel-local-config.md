# Cloudflare Tunnel — Local Config YAML Ingress Management

## Background

Modern cloudflared (2024+) tunnels can be managed either:
1. **Remotely** — via Cloudflare dashboard (default, no local config file)
2. **Locally** — via a `config.yml` file passed with `--config` flag

The default `cloudflared tunnel run <name>` fetches ingress rules from the Cloudflare API. To use a local config instead (or to add rules not yet in the dashboard), create a config.yml and update the systemd unit.

## Config File Structure

```yaml
tunnel: <tunnel-uuid>
credentials-file: /home/sc/.cloudflared/<tunnel-uuid>.json

ingress:
  - hostname: myapp.codeovertcp.com
    service: http://localhost:3001
  - hostname: api.codeovertcp.com
    service: http://localhost:8642
  - hostname: dashboard.codeovertcp.com
    service: http://localhost:9119
  # ... any number of hostname → service mappings
  # Catch-all — MUST be last, returns 404 for unmatched hostnames
  - service: http_status:404
```

## Finding the Tunnel UUID

The tunnel credentials JSON contains the UUID. It lives at `~/.cloudflared/<uuid>.json`:

```json
{"AccountTag":"...","TunnelSecret":"...","TunnelID":"<uuid>","Endpoint":""}
```

The UUID is also visible in `cloudflared tunnel list` output (if the cert.pem exists).

## Updating the Systemd Service

Find the tunnel's systemd user service (usually at `~/.config/systemd/user/<name>.service`):

```ini
[Service]
Type=simple
ExecStart=/usr/local/bin/cloudflared tunnel --config /home/sc/.cloudflared/config.yml run <tunnel-name>
```

Then reload and restart:

```bash
systemctl --user daemon-reload
systemctl --user restart <tunnel-service>
```

## Verify

Check the process is using the config file:

```bash
journalctl --user -u <tunnel-service> --no-pager -n 5
# Look for: Settings: map[config:/home/sc/.cloudflared/config.yml ...]
```

## DNS Record (Separate Step)

The local config tells cloudflared ***how*** to route traffic once it arrives at the tunnel. But DNS must first point the hostname at the tunnel. Create a CNAME record in Cloudflare DNS:

```
CNAME <hostname> → <tunnel-uuid>.cfargotunnel.com
```

This is a one-time manual step unless you have the Cloudflare API token.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `cloudflared tunnel run` ignores config file | Missing `--config` flag | Add `--config /path/to/config.yml` to ExecStart |
| `ERR Request failed` with `ingressRule=N` in logs | Backend service on that port isn't running | Start the service or check it's on the right port |
| DNS resolves but connection times out | No ingress rule matches, or no CNAME record | Check config.yml hostname matches, and DNS CNAME exists |
| Old PID still running after restart | systemd sent SIGTERM but process didn't die | Wait, or `pkill -f "cloudflared tunnel"` and let systemd restart |
