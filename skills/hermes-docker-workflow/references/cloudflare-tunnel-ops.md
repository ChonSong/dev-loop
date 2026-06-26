# Cloudflare Tunnel Operations — Lessons Learned (May-June 2026)

## Tunnel Binary Persistence

**Problem**: `/tmp/cloudflared` is on tmpfs — wiped on reboot. Also, cloudflared auto-updates kill the running process.

**Fix**:
```bash
# Copy binary to persistent location
cp /tmp/cloudflared /home/sean/.hermes/bin/cloudflared
chmod +x /home/sean/.hermes/bin/cloudflared

# Always use --no-autoupdate
/home/sean/.hermes/bin/cloudflared --no-autoupdate tunnel run \
  --credentials-file /home/sean/.cloudflared/<tunnel>-creds.json \
  --url http://<origin> <tunnel-name>
```

## Systemd User Services (No Sudo Required)

Systemd user services survive reboots and auto-restart on crashes — better than nohup or cron watchdogs.

```ini
# ~/.config/systemd/user/cloudflared-<name>.service
[Unit]
Description=Cloudflare Tunnel for <name>
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/home/sean/.hermes/bin/cloudflared --no-autoupdate tunnel run --credentials-file /home/sean/.cloudflared/<name>-creds.json --url http://<origin> <tunnel-name>
Restart=always
RestartSec=5
StandardOutput=append:/home/sean/.hermes/logs/cloudflared-<name>.log
StandardError=append:/home/sean/.hermes/logs/cloudflared-<name>.log

[Install]
WantedBy=default.target
```

Enable: `systemctl --user enable --now cloudflared-<name>`

## Cloudflare 401 Challenge Injection

**Problem**: Cloudflare injects JS challenges (`/cdn-cgi/content?id=...`) into 401 responses. This breaks browser basic auth — the browser never shows the login prompt because Cloudflare intercepts with a challenge page.

**Fix**: Don't return 401. Instead, return 200 with a login form that POSTs to set a session cookie. Then proxy authenticated requests to the backend.

**Key**: `SameSite=Lax` (not `Strict`) — browsers block `Strict` cookies on WebSocket connections initiated from JS.

## WebSocket Proxy Pattern

Streamlit's JS creates WebSocket connections via `new WebSocket(url)`. The URL is constructed from `window.location`. Browsers send same-origin cookies automatically on WebSocket connections (even `HttpOnly` ones).

**Proxy requirements**:
1. Detect `Upgrade: websocket` + `Connection: Upgrade` headers
2. Compute `Sec-WebSocket-Accept` from client's key (SHA1 of key + magic GUID, base64)
3. Return 101 Switching Protocols
4. Bidirectionally tunnel raw TCP via `select.select()`

## Auth Inside Streamlit (Preferred over Proxy Auth)

Put auth directly in the Streamlit app using `st.session_state` — avoids all proxy/WebSocket/cookie issues:

```python
# After imports, before st.set_page_config
if not st.session_state.get("_authenticated", False):
    st.set_page_config(page_title="Login", layout="centered")
    with st.form("login"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Log In"):
            if u == "sa" and p == "dawnofdarren":
                st.session_state["_authenticated"] = True
                st.rerun()
            else:
                st.error("Invalid credentials")
    st.stop()
```

## Tunnel Ingress Config via API

Use `/cfd_tunnel/` (not `/tunnel/`) for the configurations endpoint:
```bash
curl -X PUT "https://api.cloudflare.com/client/v4/accounts/<ACCT_ID>/cfd_tunnel/<TUNNEL_ID>/configurations" \
  -H "X-Auth-Email: <email>" -H "X-Auth-Key: <key>" \
  -H "Content-Type: application/json" \
  -d '{"config":{"ingress":[
    {"hostname":"example.com","service":"http://localhost:8080"},
    {"service":"http_status:404"}
  ]}}'
```

## Cloudflare Access App Conflicts

If a CF Access app exists for a hostname, it intercepts ALL requests and redirects to Access login. Delete it for custom auth:
```bash
curl -X DELETE "https://api.cloudflare.com/client/v4/accounts/<ACCT_ID>/access/apps/<APP_ID>" \
  -H "X-Auth-Email: <email>" -H "X-Auth-Key: <key>"
```

## Disk Full → Cascading Failures

At 100% disk: tunnel crashes, systemd services get masked, credentials files can't be written.
Safe cleanup: state-snapshots, .playwright cache, sync-work cache, `docker image prune -f`.

## Key Identifiers (June 2026)

| Item | Value |
|------|-------|
| Account ID | `fd4058c7aa1da2cb3ec2f2c9f028c022` |
| Zone ID | `a0dc1c2d5a810fabb43cb596a7e4b322` |
| Global API Key | `4551f6bda4835ee658c81221ee8783c9e7af3` |
| Auth Email | `Seanos1a@gmail.com` |
| hermes-webui Tunnel | `93328a7a-43ea-4329-99d9-92d9a717dfcc` |
| onetag Tunnel | `b02e5bb6-4324-4e40-a624-e21cd128f305` |
| cloudflared binary | `/home/sean/.hermes/bin/cloudflared` |
