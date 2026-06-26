# Cloudflare Tunnel — Lessons Learned (June 2026)

## Root Causes of Tunnel Death

### 1. /tmp is tmpfs
Cloudflared binary in `/tmp` gets wiped on reboot. **Always** use `/home/sean/.hermes/bin/cloudflared`.

### 2. Auto-update kills running process
Auto-update replaces the binary in-place, killing the running tunnel. **Always** pass `--no-autoupdate`.

### 3. Disk full prevents restart
When disk is 100% full, cloudflared can't write logs or state files and dies. Check `df -h /` first.
- Clean targets: `state-snapshots/`, `.playwright/`, `cache/sync-work/`, Docker images

### 4. Systemd service gets disabled
Another agent or user may disable systemd services. Check both:
```bash
systemctl --user is-enabled <service>
systemctl --user is-active <service>
```

### 5. Network unreachable
Host losing internet drops all connections. Process may not recover if restart happens before network is back.

## Missing Ingress Rule = 404

If a hostname returns 404 through tunnel (but origin works locally), the ingress config is missing the hostname. The catch-all `http_status:404` matches instead.

**Fix via API** (use `cfd_tunnel` not `tunnel`):
```bash
curl -s -X PUT "https://api.cloudflare.com/client/v4/accounts/<ACCT_ID>/cfd_tunnel/<TUNNEL_ID>/configurations" \
  -H "X-Auth-Email: <EMAIL>" -H "X-Auth-Key: <KEY>" \
  -H "Content-Type: application/json" \
  -d '{"config":{"ingress":[
    {"hostname":"hermes.codeovertcp.com","service":"http://172.19.0.2:8787"},
    {"hostname":"skills.codeovertcp.com","service":"http://172.19.0.2:8787"},
    {"hostname":"wiz.codeovertcp.com","service":"http://localhost:8080"},
    {"hostname":"onetag.codeovertcp.com","service":"http://127.0.0.1:8501"},
    {"service":"http_status:404"}
  ]}}'
```

## Multi-Tunnel Setup
Each named tunnel needs its own cloudflared process + systemd user service. One process cannot run multiple named tunnels.

## HTTP Basic Auth Proxy
For apps without built-in auth (e.g. Streamlit), use a Python proxy wrapper:
- App on internal port (e.g. 8502), auth wrapper on exposed port (e.g. 8501)
- Wrapper checks `Authorization: Basic` header before proxying
- See: `/home/sean/workspace/forrest-plan-and-track/streamlit_onetag/auth_wrapper.py`

## SSH nohup Pattern
SSH sessions with `nohup ... &` often timeout. Use a script file instead:
```bash
cat > /tmp/start.sh << 'EOF'
#!/bin/bash
pkill -f "process-name" 2>/dev/null; sleep 2
nohup /path/to/binary args > /tmp/log 2>&1 &
EOF
scp /tmp/start.sh host:/tmp/ && ssh host 'bash /tmp/start.sh'
```

## DNS CNAME Must Match Tunnel ID
After recreating a tunnel, update DNS CNAME to new tunnel ID: `<TUNNEL_ID>.cfargotunnel.com`

## Cloudflare Access App
If `/cdn-cgi/access/login` returns 404, the Access app for that hostname is misconfigured. Check via:
```bash
curl -s "https://api.cloudflare.com/client/v4/accounts/<ACCT_ID>/access/apps" \
  -H "X-Auth-Email: <EMAIL>" -H "X-Auth-Key: <KEY>"
```
