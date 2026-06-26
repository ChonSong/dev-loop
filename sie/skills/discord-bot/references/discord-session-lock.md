# Discord Session Lock — Root Cause Analysis

**Date**: 2025-05-17  
**Symptom**: `hi` messages silently dropped — no response, no error  
**Duration**: ~28 minutes (11:14–11:42)  
**Resolution**: `/stop` at 11:42:56

---

## What Happened (Pattern 1)

A `/restart` command started a long-running skill review task in session `9053043d0c98` at `11:14:24`. That session ran for **25+ minutes**, making **100+ API calls** to MiniMax-M2.7 (each 15–25s). It held the `_running_agents` slot as a **non-ephemeral** session.

When `hi` arrived in Discord thread `1505390498049818705` at `11:22:17`:
1. Discord adapter called `handle_message(event)` → dispatch to gateway
2. Gateway checked `_running_agents` — the session key was blocked
3. With `_busy_input_mode: "interrupt"` (the default), the gateway called `interrupt()` and returned `None`
4. **Message silently dropped** — not queued, not retried, no error logged for the user

The gateway's staleness eviction only fires when `_handle_message` is **called** — but the `hi` never reached that point because it was blocked at the dispatch layer.

---

## Pattern 2 (May 2025): Session Cleanup Race Condition

**Symptom**: After `/stop` releases the session lock, messages still produce no response — no ACK, no error, nothing. The message reaches the gateway (`inbound message` logged) but produces no `response ready` entry.

**Root cause**: `_interrupt_and_clear_session()` (line ~13820) calls `get_pending_message()` which consumes the text batch queue. If a message arrives during this brief cleanup window, it enters `_pending_text_batches` but gets immediately consumed by the in-progress cleanup — silently dropped with no response.

**Timeline from logs**:
```
12:38:42 Flushing text batch (2 chars) for thread 1505390498049818705
12:38:43 inbound message 'hi'
12:38:52 STOP for session — agent interrupted, session lock released
12:38:57 Invalidated run generation → 11 (session_reset)
12:39:35 Flushing text batch (2 chars)
12:39:36 inbound message 'hi'
12:39:51 STOP for session — agent interrupted, session lock released
```
Notice: `inbound message 'hi'` at 12:38:43 and 12:39:36 — NO `response ready` follows either. The messages reached the gateway dispatcher but were consumed during the cleanup transition.

**Why `/new` doesn't fix it**: `/new` creates a new session, but the session cleanup race condition still applies — the message arrives during the transition and gets consumed. The underlying `busy_input_mode` (`interrupt`) is unchanged by `/new`.

---

## Root Cause Chain (Pattern 1)

```
/restart skill review task → session 9053043d0c98 starts (11:14:24)
    → non-ephemeral, holds _running_agents slot
    → makes 100+ API calls over 25+ minutes

hi arrives in Discord thread (11:22:17)
    → handle_message() dispatched to gateway
    → gateway checks _running_agents: SESSION IS LOCKED
    → _busy_input_mode: "interrupt" → interrupt() called, None returned
    → message DROPPED (no queue, no retry, no error)

User issues /reset (11:22:22)
    → _interrupt_and_clear_session(release_running_state=False)
    → generation invalidated but session re-enters _running_agents during text batch flush

Second hi arrives (11:22:33)
    → same block, same drop

User issues /stop (11:42:56)
    → _interrupt_and_clear_session(release_running_state=True)
    → session REMOVED from _running_agents
    → session lock released
    → thread responsive again
```

---

## Key Code Locations

| Component | File | Lines | Relevance |
|-----------|------|-------|-----------|
| `_running_agents` lock check | `run.py` | 5945–5992 | Staleness eviction only runs when `_handle_message` is called — blocked messages never reach here |
| `_busy_input_mode: "interrupt"` | `run.py` | ~1185 | Default: messages arriving while session is running are silently dropped |
| `interrupt()` call | `run.py` | ~6318 | When `_quick_key in _running_agents`, `interrupt()` called and `None` returned |
| `/stop` session release | `run.py` | ~13820 | `_interrupt_and_clear_session(release_running_state=True)` removes from `_running_agents` |
| `/reset` partial release | `run.py` | ~13820 | `_interrupt_and_clear_session(release_running_state=False)` only invalidates generation |
| Discord text batching | `discord.py` | 4727–4811 | 0.6s delay before `handle_message()` called; session can re-enter `_running_agents` during flush |
| `_interrupt_and_clear_session()` | `run.py` | ~13820 | Calls `get_pending_message()` — consumes and discards text batch queue |
| Thread participation | `helpers.py` | 201 | Threads in `discord_threads.json` tracked; combined with `require_mention: false` allows response without @mention |

---

## Why `/reset` Failed But `/stop` Worked

- `/reset`: `release_running_state=False` → generation invalidated, session **remains** in `_running_agents` → re-enters during text batch flush → still locked when next `hi` arrives
- `/stop`: `release_running_state=True` → session **removed** from `_running_agents` → lock released → new messages processed

---

## Config Fix — Prevent Silent Drops

**Change `busy_input_mode` in `config.yaml`:**
```yaml
display:
  busy_input_mode: queue  # instead of interrupt (default)
```

With `queue`, arriving messages are queued (not dropped) and processed after the current cleanup completes. This eliminates the race condition entirely.

**Why not `steer`?** `steer` injects messages into the running agent mid-turn, which works but depends on the agent supporting the `steer()` method. `queue` is more robust — it serializes message processing.

**The `interrupt` mode is still correct for some cases** (e.g., wanting to abort a long-running task immediately with a fresh message), but for Discord threads where messages may arrive during session transitions, `queue` prevents silent drops.

**Verification after config change:**
```bash
# Reload gateway to pick up config change
hermes restart

# Then in Discord — send "hi" and verify:
# 1. You get an ACK immediately ("Queued your message...")
# 2. After the current task finishes, you get a real response
```

---

## Other Config Fixes

**1. Reduce staleness timeout** (auto-evict stuck sessions):
```yaml
# In config.yaml or as environment variable:
hermes_agent_timeout: 300  # evict sessions idle >5 minutes
```

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

## Detection Script

Check if any session is blocking Discord threads:

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

If `active_runs > 0` and `oldest_run_age_seconds > 300`, the session may be blocking. Use `/stop` in the blocked thread to release the lock.

---

## Prevention

1. For long-running tasks that might outlive their usefulness, use `ephemeral: true` so the session doesn't hold `_running_agents`
2. Monitor `oldest_run_age_seconds` in health endpoint — values >600s for non-streaming tasks are suspicious
3. When Discord goes silent, check health before restarting gateway — if `active_runs > 0`, use `/stop` first (in the thread), not `/restart`