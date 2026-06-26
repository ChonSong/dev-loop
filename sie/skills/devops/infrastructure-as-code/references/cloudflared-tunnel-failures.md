# Cloudflared Tunnel Failure Reference

## Failure Modes

### 1. Duplicate processes → 502 after Auth (documented in SKILL.md)

**Symptom:** Browser reaches Access login, authenticates, then 502 Bad Gateway.
**Root cause:** Multiple cloudflared processes with the same tunnel credentials fighting over the control stream.
**Fix:** `pkill -f cloudflared; sleep 2;` then start exactly one.

---

### 2. Stale credentials → `control stream encountered a failure while serving` (NEW)

**Symptom:** Tunnel process stays running but emits a repeating loop:
```
ERR failed to run the datagram handler error="context canceled"
ERR failed to serve tunnel connection error="control stream encountered a failure while serving"
INF Retrying connection in up to 8s
```
Exponential backoff increases retry delay indefinitely. Cloudflare dashboard shows tunnel as "healthy" or "degraded" but no traffic is routed.

**Root cause:** Tunnel was deleted and recreated in Cloudflare dashboard. The `credentials_file` on disk contains a `TunnelID` that no longer exists server-side. The tunnel registers enough to appear "healthy" but the control stream handshake fails on every attempt.

**Fix:**
1. Delete the stale tunnel in **Cloudflare Zero Trust → Networks → Tunnels**
2. Create a fresh tunnel named `hermes-webui` (Cloudflare Zero Trust legacy connector)
3. Download the new credentials JSON
4. Deploy with the new credentials file:
   ```bash
   kill <old_pid>
   /tmp/cloudflared tunnel run \
     --credentials-file /home/sean/.cloudflared/hermes-webui-creds.json \
     --url http://172.19.0.2:8787 hermes-webui
   ```

**Key diagnostic command** (from host):
```bash
curl -s "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/tunnels" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" | \
  python3 -c "import json,sys; [print(t['name'], t['id'], t['status']) for t in json.load(sys.stdin)['result']]"
```

If the tunnel name doesn't appear in the API response but the credentials file has a TunnelID, the creds are stale.

**Credential file locations on this host:**
- `/home/sean/.cloudflared/hermes-webui-creds.json` — primary (TunnelID: `bf723d4c-7299-4a6b-a2f9-6cee6bec86dc`)
- `/home/sean/.cloudflared/hermes-webui-argo-token.txt` — argo token format (base64, `eyJh...` prefix)
- `/home/sean/.cloudflared/hermes-webui-argo-token.txt` — alternative token

---

### 3. Token vs Credentials confusion

| Approach | File | Command syntax |
|---|---|---|
| Credentials file | `*creds.json` | `cloudflared tunnel run --credentials-file /path/to/creds.json <tunnel_name>` |
| Token file | `*token.txt` | `cloudflared tunnel run --token-file /path/to/token.txt` |

Using `--credentials-file` with an Argo token (base64) file causes an immediate error. Using `--token-file` with a credentials JSON causes an immediate error. Match the file type to the flag.

---

## Session Transcript (2026-05-26)

**Problem:** hermes.codeovertcp.com returned Error 1033 (Cloudflare "Unknown error"). Cloudflare Access login page loaded, but after email OTP authentication, the browser showed 1033 instead of the app.

**Investigation:**
- `curl https://hermes.codeovertcp.com` from host → 200 OK
- Localhost:8787 → 200 OK  
- Tunnel process (PID 2181128) had been running 44 minutes
- Log showed repeating `control stream encountered a failure while serving` loop

**Root cause:** Tunnel credentials on disk (`bf723d4c-7299-4a6b-a2f9-6cee6bec86dc`) did not match any active tunnel in Cloudflare Zero Trust. The tunnel had been deleted/replaced but the creds file was never updated.

**Tunnel processes running:**
- `65532 root: cloudflared --no-autoupdate tunnel run --token-file /etc/cloudflared/agent-os-argo-token.txt --url http://backend:3001` (agent-os tunnel, different tunnel)
- `2181128 sean: /tmp/cloudflared tunnel run --credentials-file /home/sean/.cloudflared/hermes-webui-creds.json --url http://172.19.0.2:8787 hermes-webui` ← stale
