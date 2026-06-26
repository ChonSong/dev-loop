---
name: deployment-audit
description: Verify that a deployed web application is serving the correct codebase with all services healthy. Catch the "wrong app on the right URL" failure mode — the most common preventable deployment error.
---

# Deployment Audit

## When to Use

Trigger whenever:
- You just deployed a web app and need to confirm it's working correctly
- The user reports a broken/empty/502 site and you're investigating
- You're about to make deployment infrastructure changes and need a baseline
- You're handed off a project and need to understand what's actually running vs what should be
- The user asks for a comprehensive system state review, session audit, or "how are we doing?" assessment (see `references/comprehensive-system-audit.md` for the full multi-dimensional pattern)

## Audit Checklist

Execute these steps **in order**. Stop and flag any failure before proceeding.

### 1. Port & Process Inventory

Identify everything listening on the relevant ports:

```bash
# Identify processes on target ports (works without ss/ps in containers)
find /proc -maxdepth 2 -name "cmdline" 2>/dev/null | while read cmd; do
  if grep -qa "8003\|8564\|3000\|8555\|3001" "$cmd" 2>/dev/null; then
    echo "$(echo $cmd | cut -d/ -f3): $(tr '\0' ' ' < $cmd 2>/dev/null)"
  fi
done

# Alternative: check which ports are actually in use
cat /proc/net/tcp /proc/net/tcp6 2>/dev/null | awk '{print $2}' | grep -E ':1F40|:2174|:0BB8|:216B|:0BB9' | head -10
```

Key check: **Don't just check that something is running. Check WHAT is running.** A running server that serves the wrong app is worse than a dead server.

### 1b. Systemd Service Audit (Host-Managed Deployments)

If services run on the **host** (not inside the container), verify systemd units are active:

```bash
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 "
echo '=== Systemd status ==='
systemctl --user --no-pager is-active <service1> <service2> 2>/dev/null
echo ''
echo '=== Restart policy ==='
systemctl --user --no-pager show <service> -p Restart 2>/dev/null | head -3
echo ''
echo '=== Recent restarts ==='
systemctl --user --no-pager list-timers 2>/dev/null | head -5
"
```

**Key signals:**
- `active (running)` — service is up
- `Restart=always` — auto-recovery on crash (cron watchdogs redundant)
- `loaded (/home/sean/.config/systemd/user/...; enabled; preset: enabled)` — survives host reboot
- `activating (auto-restart)` — service keeps crashing, systemd is retrying

**When systemd is active, cron watchdogs are redundant.** A 5-minute health-check cron adds zero recovery value when the service already has `Restart=always`. Reduce frequency or switch to `no_agent: true` script mode.

### 2. Codebase Path Verification

Find where the serving process was started from:

```bash
# For each process on target ports, get its cwd
ls -la /proc/<PID>/cwd
# And its root
ls -la /proc/<PID>/exe
```

Compare the resolved path to where you expect the app to be. **If the path doesn't match the intended codebase repo, the wrong app is deployed.**

Common failure mode: two codebases in the same environment (e.g., `open-lovable/` and `gto-wizard-clone/`) and the wrong one got started on the target port.

### 3. HTTP Title Tag Verification

The HTML `<title>` tag is a definitive fingerprint. Extract it and compare to expectations:

```bash
curl -sL http://localhost:<PORT>/ 2>/dev/null | grep -o '<title>[^<]*</title>' | head -1
```

Expected patterns:
- "GTO Wizard" → correct for wiz.codeovertcp.com
- "Open Lovable v3" → WRONG for that URL
- "Welcome to Next.js!" → scaffolding that wasn't customized

**If the title is wrong, stop and fix the deployment before proceeding.** This is the single most reliable check.

### 4. API Health Endpoint

Every production API should have a health endpoint:

```bash
curl -s http://localhost:<API_PORT>/health 2>/dev/null
curl -s http://localhost:<API_PORT>/api/v1/health 2>/dev/null
```

Check for:
- HTTP 200 (not 404, 502, 500)
- JSON response with `"status": "healthy"` or similar
- Database connectivity reported (if applicable)

### 5. DNS Resolution Check

Check whether the domain actually resolves to the tunnel or to Cloudflare before assuming the tunnel is the problem.

```bash
# What does DNS say?
dig +short <domain>
nslookup <domain>

# Expected for Cloudflare tunnel: resolves to Cloudflare IPs (104.x.x.x, 172.x.x.x)
#   or CNAME to your tunnel endpoint (e.g. tunnel-id.cfargotunnel.com)
# Unexpected: resolves to an arbitrary IP (20.x.x.x, 5.x.x.x, etc.) — DNS record
#   likely missing or pointed somewhere else
# Error / NXDOMAIN — no DNS record at all

# Check if the domain is proxied through Cloudflare:
curl -sI https://<domain>/ 2>/dev/null | grep -i 'cf-ray\|server: cloudflare'
# If you get a response with CF-Ray header, DNS → Cloudflare is working.
# If ERR_CONNECTION_REFUSED or wrong IP, DNS is the problem.
```

**Common DNS failure modes for tunnel services:**

| Symptom | Likely Cause |
|---------|-------------|
| Domain resolves to random IP (e.g. `20.11.40.34`) | DNS A record exists but was set before tunnel was created — never updated to CNAME |
| `ERR_CONNECTION_REFUSED` at URL | DNS doesn't point to Cloudflare at all — no CNAME to tunnel endpoint |
| `ERR_SSL_VERSION_OR_CIPHER_MISMATCH` | DNS points to Cloudflare but no cert/proxy enabled (grey cloud instead of orange) |
| `502 Bad Gateway` from Cloudflare | DNS OK, tunnel running, but tunnel service doesn't match what's at the port |
| `Cloudflare 520/521/522` | DNS OK, tunnel configured, but backend service is down |

**To fix the DNS record (Cloudflare dashboard):**
```
Type: CNAME
Name: <subdomain (e.g., hex)>
Target: <tunnel-id>.cfargotunnel.com
Proxy status: Proxied (orange cloud)
```

**Cloudflare API limitation:** Tunnel credentials (`cfut_*` API tokens from `cert.pem`) are scoped to tunnel operations only. They return `9106 Authentication failed` on DNS API endpoints. You need a separate API token with `Zone:DNS:Edit` permission, or use the Cloudflare dashboard.

**Extracting tunnel metadata from cert.pem (useful for debugging):**
```python
import base64, json
with open('~/.cloudflared/cert.pem') as f:
    raw = f.read()
b64 = ''.join(line.strip() for line in raw.strip().split('\n')
              if not line.startswith('---'))
decoded = json.loads(base64.b64decode(b64 + '=' * (4 - len(b64) % 4)))
# Returns: {"zoneID": "...", "accountID": "...", "apiToken": "cfut_..."}
# apiToken is tunnel-only — not valid for DNS operations.
```

### 6. Tunnel / Reverse Proxy Audit

If the app is served through a tunnel (Cloudflare, ngrok, etc.), only run this after DNS checks pass:

```bash
# Find tunnel config
find / -name "*tunnel*config*" -o -name "*cloudflared*config*" 2>/dev/null | grep -v node_modules

# Check what the tunnel IS routing to (extract from config)
grep "service:" <config-file>

# Check what the tunnel SHOULD be routing to (compare to step 4)
```

**Critical check:** The tunnel ingress must route BOTH frontend AND API paths. Missing API routes are a common silent failure — the page loads but all data calls fail.

**Tunnel is running but site is down?** If DNS passes but the site is still unreachable, verify the tunnel is connected:
```bash
# Check tunnel status
ps aux | grep cloudflared
# Check for recent errors in tunnel logs
journalctl --user -u cloudflared-* --no-pager -n 20 2>/dev/null
```

### 7. End-to-End Smoke Test

```bash
# Hit the live URL (for tunnels) or local port
curl -sI https://yourdomain.com/ | head -5
status=$(curl -s -o /dev/null -w "%{http_code}" https://yourdomain.com/)
echo "HTTP $status"

# If the site returns 3xx, follow the redirect
curl -skL https://yourdomain.com/ 2>/dev/null | grep -o '<title>[^<]*</title>'

# Check API through tunnel
curl -s https://yourdomain.com/api/v1/health 2>/dev/null
```

### 8. Database Check (if applicable)

```bash
# Verify DB file exists and has data
ls -la <db-path>
sqlite3 <db-path> ".tables" 2>/dev/null
sqlite3 <db-path> "SELECT COUNT(*) FROM <key-table>;" 2>/dev/null
```

## Pitfalls

- **Title-based verification is mandatory.** A server that responds with HTTP 200 but serves the wrong app is the most common deployment error. Always check `<title>`.
- **Process existence ≠ correct app.** PID 16020 running `next dev -p 8564` could be serving `open-lovable/` or `gto-wizard-clone/`. Check the process cwd.
- **Tunnel configs proliferate.** You may find 3-5 config files for the same tunnel. The active one is the one the running `cloudflared` process loaded. Check `ps` for the `--config` argument.
- **Port conflicts.** A port may be occupied by an unrelated service (e.g., Chrome network service on 8002). Verify the process name, not just the port.
- **API routes in tunnels are often forgotten.** The frontend loads fine but all API calls return 404. Always check that `/api/*` is routed separately.
- **Multiple codebases with similar purpose.** When two repos serve different versions of the same app, it's easy to start the wrong one. Track which codebase was last deployed.
- **Host vs container process conflict.** In containerized deployments, the HOST may have its own process on the same port serving a stale build, while the container also has a process. `curl localhost:<PORT>` from inside the container may reach the container's service, but from the HOST it reaches the host's process — and they can be different builds. After killing container processes, verify from BOTH the container AND host perspective that the port is free and the right process restarts. Use `ssh user@host pgrep -af "next|uvicorn"` to check for host-side zombie processes, which can accumulate as `<defunct>` entries. A defunct process doesn't serve traffic but prevents the port from being freed — kill its parent to clean it up.
- **Host process auto-restart.** The host may have a systemd user service or startup script that auto-restarts the frontend when killed. If you kill a process on the port and a new PID appears seconds later, an auto-restart is active. Workaround: run the container frontend on a different port and update the tunnel config, or disable the auto-restart on the host (`systemctl --user disable --now <service>`).
- **Zombie/defunct next-server processes accumulate.** Each time a Next.js server is killed without properly terminating its process group, a `<defunct>` entry stays in the process table. These don't serve traffic but clutter the process table. Kill them by their parent PID.
- **Screenshots catch what curl misses.** `curl` may return 200 even when the page renders incorrectly (CSS mismatch, blank client-rendered content, empty state with no error). After passing the curl checks, take a headless Chrome screenshot to verify visual fidelity. Compare against reference screenshots when available. Use `google-chrome-stable --headless --screenshot=<path> --window-size=1440,900 <URL>` from the host.
- **Cloudflare tunnel API tokens can't manage DNS.** The `cfut_*` token embedded in `cert.pem` is scoped to tunnel operations only. Calling the DNS API with it returns `9106 Authentication failed`. Adding a new subdomain requires either the Cloudflare dashboard or a separate API token with `Zone:DNS:Edit` permission. Don't waste time trying to script DNS creation with the tunnel token.
- **DNS can appear to work locally while being wrong globally.** `dig`/`nslookup` may return cached results or the wrong IP. Cross-check against what Cloudflare API says the DNS records are. If the domain resolves to an IP that isn't a Cloudflare range (104.x.x.x, 172.x.x.x), the DNS CNAME record is missing or pointing somewhere else entirely.

## Verification

Before saying "deployment is complete" or "the site is up":

1. ✅ DNS resolves domain to Cloudflare tunnel (CNAME to tunnel endpoint)
2. ✅ Title tag matches expected app name
3. ✅ API health endpoint returns 200
4. ✅ Tunnel routes both `/` and `/api/*`
5. ✅ End-to-end: hit the public URL, get a page that works
6. ✅ Database is accessible (if applicable)
7. ✅ The deployment config (ports, paths, tunnel) is documented in `deployment-info.md` or equivalent



## Linked References

The deployment-audit skill includes these reference files for specialized audit patterns:

| File | Scope |
|------|-------|
| `references/comprehensive-system-audit.md` | Full-stack system health investigation: session context, cron audit, skills infra, disk, git/auth, autonomous pipeline, priority synthesis |
| `references/multi-system-audit-pattern.md` | Parallel health checks across multiple deployed systems |
| `references/wiz-codeovertcp-audit.md` | Worked example: GTO Wizard deployment audit |
| `references/hwc-QA.md` | QA checklist for hermes-web-computer: health/SPA/binary freshness/frontend staleness checks across the container-host boundary |



## Linked References
