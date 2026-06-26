# Discord Bot Unresponsive — Diagnostic Reference

## Session Context

Gateway restarted at 11:13:56. Discord connected as `oclaws#7871` at 11:14:02.
Inbound `hi` received at 11:14:13 — no response delivered.
Active session `9053043d0c98` running (64+ API calls made, phase: running).
Gateway log stopped updating at 11:14:13 despite active session.
`/reset` in Discord thread resolved the issue.

## Diagnostic Framework

When Discord bot receives messages but does not respond:

### 1. Check Gateway Health
```bash
curl -s "http://localhost:8787/health" | python3 -m json.tool
```
Look for: `active_runs`, `active_streams`, session IDs and their phase.

### 2. Check Gateway Log
```
tail -50 /home/hermeswebui/.hermes/logs/gateway.log
```
Key markers to find:
- `inbound message: platform=discord` — gateway received the message
- `Sending response` — gateway delivered output to Discord
- `Flushing text batch` — batching completed before flush

**Gateway log freeze pattern**: If the log shows the inbound message but no
subsequent `Sending response` entry, the agent produced output but the gateway
failed to deliver it. Check if the session is still running (health) and whether
the session is streaming to the correct platform channel.

### 3. Check Agent Log
```
grep "session_id" /home/hermeswebui/.hermes/logs/agent.log | tail -20
```
Active sessions show phase: running. If phase is stuck, the agent loop may be
hung on a long-running call.

### 4. Check Errors Log
```
tail -20 /home/hermeswebui/.hermes/logs/errors.log
```
Title generation 404s are auxiliary (not main chat path) — they won't cause
total silence but indicate config issues. Fix: ensure `custom_providers[minimax].base_url`
is `https://api.minimax.io/v1` (not `http://localhost:4001/v1`).

### 5. Try /reset First
```
/reset
```
in the Discord thread clears stale session state and starts fresh. Often
resolves unresponsive bot without full gateway restart.

### 6. Full Restart (if /reset fails)
```
/restart
```
SIGTERM → gateway reconnects → Discord reconnects. More disruptive but
clears all session state.

## Session State vs. Gateway State

A session can be `phase: running` in the health endpoint while the gateway log
shows no new entries. This means the agent is processing (making API calls)
but the gateway is not delivering output to Discord. Possible causes:

1. **Session state corruption** — session output not flushing to platform
2. **Gateway log rotation** — log file being rewritten, appears frozen
3. **Platform delivery failure** — gateway knows about Discord but can't reach it

**Verification**: If health shows `active_streams: 1` and session is running
but gateway log hasn't updated in >2 minutes, try `/reset`. If that doesn't
work, `/restart`.

## Pre-restart Log vs. Post-restart Log

The `Flushing text batch (N chars)` entry at 11:14:12 is a pre-restart event.
Post-restart, the gateway logged:
```
inbound message: platform=discord user=Alto chat=1505390498049818705 msg='hi'
```
but no corresponding flush or send. Compare timestamps to establish
causality (was the flush before or after the restart?).

## Config Issues That Cause 404s

404s in title generation or auxiliary calls = wrong `base_url` in `custom_providers`:
- **Wrong**: `http://localhost:4001/v1` (local proxy not running)
- **Correct**: `https://api.minimax.io/v1`

Fix: update `/home/hermeswebui/.hermes/config.yaml`, then `/restart`.

## Recovery Priority

1. `/reset` — least disruptive, clears session state
2. `/restart` — clears all state, reconnects Discord
3. Investigate log divergence (session running but gateway silent)