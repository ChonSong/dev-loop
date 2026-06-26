# GTO WIZARD CLONE — Deployment Architecture (2026-08)

## Problem: Two Separate Frontends

The workspace contains TWO frontends. Only ONE should be deployed.

| Frontend | Path | Deploy? |
|----------|------|---------|
| `open-lovable/app/gto/` | Template/prototype. Title: "Open Lovable v3" | ❌ NEVER deploy this |
| `apps/web/` (gto-wizard-clone) | Real app. Title: "GTO Wizard" | ✅ This is the one |

**Quick diagnostic**: `curl -s https://wiz.codeovertcp.com/ | grep '<title>'` should show "GTO Wizard". If it shows "Open Lovable v3", you deployed the wrong app.

## Problem: Port 8002 Claimed by Chrome Network Service

Inside the Hermes container, Chrome's `network.mojom.NetworkService` binds to port 8002. This is NOT killable — Chrome processes are container-managed.

**Symptom**: `ERROR: [Errno 98] address already in use` even after `fuser -k 8002/tcp`.

**Diagnosis**:
```bash
for pid in $(ls /proc | grep -E '^[0-9]+$'); do
  if cat /proc/$pid/net/tcp 2>/dev/null | grep -q "1F42"; then
    echo "PID $pid: $(cat /proc/$pid/cmdline 2>/dev/null | tr '\0' ' ')"
  fi
done
```
Chrome processes (headless=new, type=utility) will appear.

**Fix**: Use port 8003 for the API:
```bash
cd workspace/gto-wizard-clone
PYTHONPATH="apps/api:packages/poker-core/src" uvicorn main:app --host 0.0.0.0 --port 8003
```

Then set `NEXT_PUBLIC_API_URL=http://localhost:8003` for the web app.

## Problem: Hermes Init Auto-Starts open-lovable on Port 8564

The Hermes init system auto-starts `next dev -p 8564` in the open-lovable directory. This claims port 8564.

**Fix**: Kill the old processes:
```bash
ps aux | grep "next" | grep "8564"
kill -9 <PIDs>
```

## Problem: cloudflared Tunnel Config Caching

The cloudflared tunnel caches its ingress config at the Cloudflare edge. Editing the local config file does NOT update the tunnel — the edge keeps serving the old config until the cloudflared process restarts and re-registers.

**Fix**:
1. Kill ALL cloudflared processes: `pkill -9 -f cloudflared`
2. Wait 2 seconds
3. Start fresh: `cloudflared --config /workspace/gto-wizard-config.yml tunnel run`
4. Wait 10 seconds for tunnel to register new config

## Problem: Quiz Random Pydantic Validation Error

The `/api/v1/quiz/random` endpoint crashed with a pydantic validation error on the `options` field (expected list, got dict).

**Root cause**: The `options` JSON column returns a string from SQLite, but the code checked for `dict` instead of `list`.

**Fix** (in `routers/quiz.py`):
```python
options=spot.options if isinstance(spot.options, list) else json.loads(spot.options) if isinstance(spot.options, str) else []
```

## Correct Start Sequence

1. Kill port conflicts
2. Start API on port 8003
3. Build web app: `next build`
4. Start web app: `NEXT_PUBLIC_API_URL=http://localhost:8003 next start -p 3000`
5. Start tunnel: `cloudflared --config /workspace/gto-wizard-config.yml tunnel run`
6. Verify: `curl -s https://wiz.codeovertcp.com/ | grep '<title>'` → "GTO Wizard"
