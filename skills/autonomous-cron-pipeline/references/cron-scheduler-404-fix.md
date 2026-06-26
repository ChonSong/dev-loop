# Cron Scheduler — 404 Trigger Bug + Delivery System Findings

**Date:** May 15, 2026  
**Discovery:** Scheduler has no `POST /api/jobs/{id}/run` endpoint (HTTP 404 on all trigger attempts)

---

## The `cronjob run` 404 Error

**Symptom:**
```
cronjob action=run job_id=85d63c9f073a
→ ⚠️ Cron job 'hermes-web-computer: Phase Engine (60m)' failed
   RuntimeError: HTTP 404: 404 page not found
```

**Root cause:** The scheduler's aiohttp server (port 8787) has no job-trigger route. The cron tool issues:
```
POST http://localhost:8787/api/jobs/{id}/run
```
But the scheduler never registered this route. The scheduler IS running (responds to `/health` with 200), but lacks the job execution trigger endpoint.

**Verification:**
```bash
curl -s -o /dev/null -w '%{http_code}' http://localhost:8787/         # → 200 (scheduler up)
curl -s -o /dev/null -w '%{http_code}' http://localhost:8787/health     # → 200 (health check)
curl -s -X POST http://localhost:8787/api/jobs/85d63c9f073a/run       # → 404 (no route)
curl -s http://localhost:8787/api/jobs                                # → 404 (no route)
```

**Scheduler process info:**
- PID: 28008 (found via `/proc` scanning for `HERMES_WEBUI_PORT=8787`)
- Env: `HERMES_WEBUI_STATE_DIR=/home/hermeswebui/.hermes/webui`, `HERMES_WEBUI_PORT=8787`
- Socket: `/tmp/hermes_rpc_*.sock` (Unix RPC socket, not HTTP)

**Timer firing:** WORKS. Jobs scheduled with `* * * * *` fire on schedule and update `last_run_at` / `last_status` correctly. Only `cronjob run` (manual trigger) is broken.

**Workaround:** `delegate_task` — immediate execution, results visible in current session. This is the recommended execution engine.

---

## The `deliver` Field Is Client-Side Only

**Critical finding:** The `deliver` field (`origin`, `discord`, `all`, `local`) is processed by the **cron tool** (client-side `cronjob_tools.py`), not the **scheduler** (server-side `cron/scheduler.py`).

The scheduler delivers via `web.deliver()` (internal session routing) only. It has no Discord, Telegram, or platform delivery code.

| `deliver` value | What happens |
|-----------------|-------------|
| `local` | Output stored to filesystem, never pushed to user |
| `origin` | Resolves to creating session ID at fire time. If session isn't active, output disappears silently. |
| `all` | Requires 2+ channels wired. With fewer, logs `"no delivery target resolved for deliver=all"` and discards output (no local fallback). |
| `discord` | **Unwired.** Accepted as config but never calls Discord API. Timer-fired jobs need `send_message` in the prompt to reach Discord. |

**Evidence:** `grep -r "deliver\|discord" /home/hermeswebui/.hermes/hermes-agent/cron/scheduler.py` → zero matches for Discord delivery.

---

## MiniMax API Endpoint Status (May 2026)

Testing from inside the container:

| Endpoint | Auth | Result |
|----------|------|--------|
| `https://api.minimax.io/v1/chat/completions` | Bearer | 404 |
| `https://api.minimax.io/v1/models` | Bearer | 401 |
| `https://api.minimax.io/llm/v1/chat/completions` | Bearer | 404 |
| `https://api.minimax.io/anthropic/v1/messages` | Bearer | 401 (needs X-Api-Key) |
| `https://api.minimax.io/anthropic/v1/messages` | X-Api-Key | 401 (key rejected) |
| `https://minimax.chat/v1/chat/completions` | Bearer | 302 → 404 |
| `https://api.minimax.chat/v1/chat/completions` | Bearer | 401 (login fail) |
| `https://api.minimax.chat/v1/chat/completions` | X-Api-Key | 401 |

**Conclusion:** The `minimax-portal` provider (using `X-Api-Key` auth to `https://api.minimax.io/anthropic`) returns 401 from inside the container. The `custom` provider points to `http://localhost:4001/v1` which is unreachable from inside the container. Both routes from inside the container fail.

The working path (from web UI sessions) is different — the web UI session uses `minimax-portal` successfully via the same container's network. This suggests the auth works from the web UI process but not from the scheduler process, possibly due to different env var resolution or a cached token that's not available in the scheduler's env.

**For cron jobs:** Use `provider: "custom"` (no explicit provider key), which resolves to the config's default without the X-Api-Key header issue. Model: `"MiniMax-M2.7"`.

---

## Job Disappearance When Repeat Limit Reached

Jobs with `repeat: "N/M"` disappear from `cronjob action=list` when N reaches M. `cronjob run` returns "not found" for disappeared jobs.

**Job `f5a499e5d25a`** (HWC Phase Engine): Started with `repeat: "2/3"`. After 2 failed runs (both 404 trigger error + 401 auth), it disappeared from the list. Recreated as `85d63c9f073a` with `repeat: "99"`.

**Always set high repeat limits** (`repeat: 99`) to prevent accidental disappearance during debugging.

---

## Scheduler Socket vs HTTP

The scheduler uses a Unix socket (`/tmp/hermes_rpc_*.sock`) for internal RPC, not HTTP. The cron tool's `cronjob run` attempts an HTTP request that the scheduler never registered. This suggests the scheduler was designed to receive triggers via Unix socket RPC (from the hermes CLI), but the cron tool implementation uses HTTP instead.

The correct trigger mechanism may be:
```python
import socket
socket_path = '/tmp/hermes_rpc_7fd47386f26d4a34824a016bc1411c7a.sock'
# Send trigger message via Unix socket
```

But `socat` is not available in this environment and the socket path rotates. The HTTP trigger approach was the intended public API — it's just not implemented yet in this version.

**Use `delegate_task` as the reliable execution engine until the HTTP trigger endpoint is added to the scheduler.**