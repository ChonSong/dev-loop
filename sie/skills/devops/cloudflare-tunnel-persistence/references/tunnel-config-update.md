# Tunnel Config Update Workflow

## Scenario: Port mapping is wrong
When a tunnel hostname routes to the wrong local port (e.g., `wiz.codeovertcp.com` → `:3030` instead of `:3000`):

### 1. Identify the wrong port
```bash
# Check tunnel config
cat ~/.cloudflared/config.yml | grep -A1 wiz

# Check what's actually listening
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/ 2>/dev/null  # → 200 (correct)
curl -s -o /dev/null -w "%{http_code}" http://localhost:3030/ 2>/dev/null  # → 000 (dead)
```

### 2. Fix the config
Use `patch` tool, not sed:
```
patch ~/.cloudflared/config.yml
old: service: http://localhost:3030
new: service: http://localhost:3000
```

### 3. Kill existing tunnel
```bash
pkill -f "cloudflared tunnel"
sleep 2
# Verify dead
ps aux | grep cloudflared | grep -v grep || echo "dead"
```
If a stale PID lingers: `kill -9 <PID>`.

### 4. Restart in background
```bash
cloudflared tunnel --config /home/sc/.cloudflared/config.yml run codeovertcp >/tmp/cloudflared.log 2>&1
```
**Must use `terminal(background=true)`** — no trailing `&` in the command string.

### 5. Verify connections
Wait ~5s for QUIC connections to establish:
```bash
tail -5 /tmp/cloudflared.log
# Should show: "Registered tunnel connection connIndex=..."
# Connections to syd05 + cbr01 via QUIC
```

### 6. Verify public endpoint
```bash
curl -s -o /dev/null -w "HTTP %{http_code} in %{time_total}s" https://wiz.codeovertcp.com/
```
Expected: `HTTP 200 in 0.1s`

## Pitfalls

| Pitfall | Fix |
|---------|-----|
| Config change not picked up | cloudflared doesn't reload config on HUP — must kill + restart |
| 502 after restart | Wrong port or service not listening on target port. Check local first |
| Two cloudflared PIDs after restart | One is the wrapper bash process (from background=true), one is real cloudflared — both fine |
| `000` HTTP code on local curl | Nothing listening on that port — start the service first |
| Tunnel token can't manage Access apps | The argo tunnel token has `tunnel:write` but not `access:edit` scope |
| Log starts fresh each restart | `/tmp/cloudflared.log` is ephemeral |