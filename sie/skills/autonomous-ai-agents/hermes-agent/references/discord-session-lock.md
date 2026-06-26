# Discord Session Lock — Silent Message Drop

**Date**: 2025-05-17  
**Symptom**: Discord messages silently dropped — no response, no error, not queued  
**Duration**: ~28 minutes  
**Root cause**: Long-running non-ephemeral session holding `_running_agents` blocks new Discord messages via `_busy_input_mode: "interrupt"`  
**Resolution**: `/stop` in Discord thread (releases running state lock)

---

## What Happened

A `/restart` command started a skill review task in session `9053043d0c98` at `11:14:24`.  
That session ran **25+ minutes**, making **100+ API calls** to MiniMax-M2.7 (each 15–25s).  
It held `_running_agents` as a **non-ephemeral** session.

When `hi` arrived in Discord thread `1505390498049818705` at `11:22:17`:
1. Discord adapter called `handle_message(event)` → dispatch to gateway
2. Gateway checked `_running_agents` — session key was blocked
3. With `_busy_input_mode: "interrupt"` (default), `interrupt()` called → `None` returned
4. **Message silently dropped** — no queue, no retry, no error

`/reset` failed because it calls `_interrupt_and_clear_session(release_running_state=False)` — only invalidates generation, session **remains** in `_running_agents` and re-enters during text batch flush.  
`/stop` succeeded because it calls `_interrupt_and_clear_session(release_running_state=True)` — **removes** session from `_running_agents` entirely.

---

## Key Code

| Component | Location | Relevance |
|-----------|----------|-----------|
| `_busy_input_mode: "interrupt"` default | `run.py` ~1185 | Messages during locked session = silent drop |
| `_running_agents` lock check | `run.py` 5945–5992 | Only fires when `_handle_message` is called — blocked messages never reach here |
| `/stop` session release | `run.py` ~13820 | `release_running_state=True` |
| `/reset` partial release | `run.py` ~13820 | `release_running_state=False` — does NOT release lock |
| Discord text batching | `discord.py` 4727–4811 | 0.6s delay before `handle_message()` called |

---

## Prevention Config

**1. Reduce staleness timeout** — auto-evict sessions idle >5 minutes:
```yaml
# In config.yaml or as environment variable:
hermes_agent_timeout: 300
```
Only evicts sessions that are both old AND idle (no recent API calls).

**2. Add Discord thread to `allowed_channels`**:
```yaml
discord:
  allowed_channels:
    - "1505390498049818705"  # guarantees response
```

**3. `custom_providers.minimax.base_url`** — must be `https://api.minimax.io/v1`, NOT `http://localhost:4001/v1`

---

## Detection

```bash
curl -s http://localhost:8787/health | python3 -c "
import json, sys
d = json.load(sys.stdin)
print('Active runs:', d.get('active_runs', 0))
for s in d.get('sessions', []):
    print(f'  {s[\"session_id\"][:8]}... phase={s[\"phase\"]} age={s.get(\"oldest_run_age_seconds\", 0):.0f}s')
"
```

If `active_runs > 0` and `oldest_run_age_seconds > 300`, use `/stop` in the blocked thread.