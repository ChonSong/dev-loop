# Discord Session Lock — Silent Message Drop Root Cause

**Session**: 2025-05-17, Discord thread `1505390498049818705`
**Symptom**: `hi` messages silently dropped — no response, no error, not queued
**Duration**: ~28 minutes (11:14–11:42)
**Resolution**: `/stop` at 11:42:56 released `_running_agents` lock

---

## Root Cause Chain

```
/restart command → starts skill review task in session 9053043d0c98 (11:14:24)
    → non-ephemeral session, holds _running_agents slot
    → runs 25+ minutes, 100+ API calls to MiniMax-M2.7 (15-25s each)

hi arrives in Discord thread (11:22:17)
    → handle_message() dispatched to gateway
    → gateway checks _running_agents: SESSION IS LOCKED
    → _busy_input_mode: "interrupt" (default)
    → interrupt() called on the locked session → None returned
    → message SILENTLY DROPPED (no queue, no retry, no error logged)

User issues /reset (11:22:22)
    → _interrupt_and_clear_session(release_running_state=False)
    → generation invalidated but session REMAINS in _running_agents
    → session re-enters _running_agents during text batch flush
    → still locked when next hi arrives

Second hi arrives (11:22:33)
    → same block, same silent drop

User issues /stop (11:42:56)
    → _interrupt_and_clear_session(release_running_state=True)
    → session REMOVED from _running_agents
    → lock released → thread responsive
```

---

## Key Finding: `/reset` Does NOT Release the Lock

`/reset` calls `_interrupt_and_clear_session(release_running_state=False)` — it only
invalidates the generation. The session stays in `_running_agents` and re-enters during
text batch flush. For Discord thread hangs, `/stop` (release_running_state=True) is
the correct tool.

---

## Why Staleness Eviction Didn't Help

The staleness eviction logic (run.py lines 5946–5992) only fires when `_handle_message` is
**called**. But the `hi` message never reached `_handle_message` — it was blocked at the
dispatch layer. The session was actively running (100+ API calls over 25 minutes), so
`seconds_since_activity` was low and eviction never triggered.

The `_running_agents` lock check happens BEFORE the staleness check, at the message
dispatch layer. Locked sessions block new messages from even reaching the handler.

---

## Config Fixes

**1. Reduce staleness timeout** (auto-evict stuck sessions):
```yaml
# In config.yaml or as environment variable:
hermes_agent_timeout: 300  # evict sessions idle >5 minutes
```
Only affects sessions that are both old AND idle (no recent API calls). Actively
running agents making progress are never evicted.

**2. Add Discord thread to `allowed_channels`**:
```yaml
discord:
  allowed_channels:
    - "1505390498049818705"  # Alto's thread — guarantees response
```

**3. Verify `custom_providers.minimax.base_url`**:
```yaml
custom_providers:
  minimax:
    base_url: https://api.minimax.io/v1  # NOT http://localhost:4001/v1
```

---

## Detection

```bash
curl -s http://localhost:8787/health | python3 -c "
import json, sys
d = json.load(sys.stdin)
print('Active runs:', d.get('active_runs', 0))
for s in d.get('sessions', []):
    age = s.get('oldest_run_age_seconds', 0)
    phase = s.get('phase', 'unknown')
    sid = s.get('session_id', '?')
    print(f'  {sid[:8]}... phase={phase} age={age:.0f}s')
"
```

If `active_runs > 0` and `oldest_run_age_seconds > 300`, the session may be blocking.
Use `/stop` in the blocked thread to release the lock.

---

## Prevention

1. For long-running tasks that might outlive their usefulness, use `ephemeral: true`
   so the session doesn't hold `_running_agents`
2. Monitor `oldest_run_age_seconds` in health endpoint — values >600s for non-streaming
   tasks are suspicious
3. When Discord goes silent, check health before restarting gateway — if `active_runs > 0`,
   use `/stop` first (in the thread), not `/restart`
4. `_busy_input_mode: "queue"` would queue new messages instead of dropping them —
   but changes gateway behavior for all platforms, not just Discord