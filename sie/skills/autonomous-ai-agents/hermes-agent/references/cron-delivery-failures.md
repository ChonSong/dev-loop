# Cron Delivery Failures — Lessons from OpenClaw

**Source:** OpenClaw session log analysis (82 sessions) + Hermes cron audit  
**Date:** 2026-04-30

---

## The Core Pattern: Output Produced, Delivery Silent

Both Night Owl (OpenClaw) and Overnight Autonomy Engine (Hermes) produced valuable output that **never reached Sean**:

```
[Agent Runs] → [Output Generated] → [Delivery Fails] → [Human Awareness: ZERO]
```

The agent treats delivery failure as non-fatal and continues the next scheduled run. The human is unaware anything happened.

---

## Night Owl (OpenClaw) — Full Silent Failure

| Attribute | Value |
|-----------|-------|
| Frequency | Every 30 min, 1–7pm Sydney (12 runs/night) |
| Output | 17KB detailed markdown reports |
| Delivery attempt | Telegram webhook |
| Delivery result | Every run: `"Delivering to Telegram requires target <chatId>"` |
| Human awareness | Zero — Sean never saw a single report |
| What it found | Exposed Gmail password, GitHub PATs, identity conflicts — all silently |

The `chatId` was never configured. The job ran successfully every time (exit 0), produced rich output, and then silently died at the delivery step.

---

## Overnight Autonomy Engine (Hermes) — False-Positive OK

| Attribute | Value |
|-----------|-------|
| Cron schedule | `0 15 * * *` (3pm Sydney) |
| Execution | `cd /home/sean/workspace && python3 scripts/overnight_engine.py` |
| Script path | **Does NOT exist in container** |
| Delivery | `deliver: local` |
| Cron status | `last_status: ok` ← **FALSE POSITIVE** |

The `ok` means "the cron scheduler ran without throwing an exception." It does NOT mean Sean received anything. The script path doesn't exist, so either the job produces no output, or the output goes somewhere no one checks.

---

## Failure Mode Map

| Mode | Symptom | Detection |
|------|---------|-----------|
| **Delivery broken** | Job runs (`last_run_at` updates), delivery fails (`last_delivery_error` set) | Check `last_delivery_error` |
| **Never runs** | `last_run_at: null` despite being scheduled | Check `last_run_at` |
| **origin resolves to dead session** | `last_run_at` updates, output disappears | Check if creating session is active |
| **`all` with single channel** | Output silently discarded | Check gateway.log for "no delivery target resolved" |
| **`cronjob run` broken** | HTTP 404 on trigger | `curl -X POST localhost:8787/api/jobs/<id>/run` |
| **Discord delivery unwired** | No error, no message | `grep "discord" cron/scheduler.py` → 0 matches |

---

## Failure Mode 1: Model Error → Empty Deliverable

**Symptom:** `last_status: error` with `"Agent completed but produced empty response (model error, timeout, or misconfiguration)"` — but the agent ran and produced text, which then got discarded during post-processing.

**Root cause:** MiniMax API returns `code: 1211 Unknown Model` when hermes-agent calls it for session summarization or title generation.

**Detection:**
```bash
grep "1211\|Unknown Model\|Session summarization failed\|Title generation failed" ~/.hermes/logs/agent.log
```

**See:** `references/minimax-api-failures.md`

---

## Failure Mode 2: Discord 401 — "Empty Response" Misdiagnosis

**Symptom:** `last_status: error` with `"Agent completed but produced empty response"` — but the agent ran and produced text. HTTP 401 Unauthorized from Discord API.

**Root cause:** Missing or invalid `DISCORD_BOT_TOKEN`. The HTTP 401 propagates as a model error, masking the real cause.

**Detection:** Check `~/.hermes/logs/gateway.log` for 401/Unauthorized errors. Verify token in `~/.hermes/.env`.

**Fix:** Set `DISCORD_BOT_TOKEN` in `~/.hermes/.env`, then `/restart`.

---

## Failure Mode 3: `deliver: origin` Goes Nowhere (No Active Session)

**Symptom:** Cron job fires, `last_run_at` updates, but no output appears anywhere.

**Root cause:** `origin` resolves to the **creating session ID** at fire time. If that session isn't active (web UI closed, context compacted, session restarted), output goes into a dead session mailbox and is never seen.

**Evidence:** `last_run_at` updates (job ran), but `deliver: origin` results vanish. `deliver: all` may give `"no delivery target resolved for deliver=all"` and output is lost.

**Fix:** Use `deliver: local` and manually verify output from filesystem. For human-visible delivery, have the job prompt itself call `send_message` (Discord/Telegram) as a tool step — don't rely on the scheduler's delivery routing.

---

## Failure Mode 4: `deliver: all` Silently Drops Output

**Symptom:** `cronjob create` with `deliver: all` succeeds (no validation error), job fires, no output appears anywhere.

**Root cause:** `all` requires multiple wired channels. If only one channel exists or none are reachable, scheduler logs `"no delivery target resolved for deliver=all"` and silently discards output — no `local` fallback.

**Detection:** Check `~/.hermes/logs/gateway.log` for "no delivery target resolved" message.

**Fix:** Use `deliver: origin` for single-channel setups.

---

## Failure Mode 5: `cronjob run` → HTTP 404 (Wrong Endpoint URL)

**Symptom:** `cronjob run <job_id>` returns `"HTTP 404: 404 page not found"` immediately. Job never executes.

**Root cause:** The cron tool calls `POST http://localhost:8787/api/jobs/{job_id}/run`, but:
- Port 8787 is the **webui server** (PID 190, Python HTTP server), NOT the scheduler's own HTTP server
- The webui server has a job runner at `POST /api/crons/run` — which works ✅
- But the cron tool uses the wrong path (`/api/jobs/{id}/run` vs `/api/crons/run`)

**Critical distinction:** The **scheduler** (PID 56) is a **threading-based Python scheduler** — it does NOT use aiohttp or run an HTTP server on port 8787. The scheduler runs jobs in-process via `run_job()`. The webui server (port 8787) is a separate Python HTTP server that proxies cron requests.

**Evidence:**
```bash
# Wrong endpoint (what cron tool uses) — 404
curl -X POST http://localhost:8787/api/jobs/<id>/run
→ {"error": "not found"} 404

# Correct endpoint (what actually works)
curl -X POST http://localhost:8787/api/crons/run \
  -H "Content-Type: application/json" \
  -d '{"job_id":"<id>"}'
→ {"ok": true, "job_id": "<id>", "status": "running"} 200
```

**Timer firing is unaffected** — scheduler runs jobs in-process on timer tick. Only manual `cronjob run` is broken.

**Fix options:**
1. **delegate_task** — works as execution engine. Results come back to current chat.
2. **Fix the cron tool** — patch the endpoint URL in `tools/cronjob_tools.py` from `/api/jobs/{job_id}/run` to `/api/crons/run` (payload uses `job_id` field, which matches the existing endpoint).
3. **Accept** — rely on timer firing only. `last_run_at` and `last_status` update correctly on each tick.

---

## Failure Mode 6: `deliver: discord` Is Unwired

**Symptom:** `deliver: discord` accepted by cron tool without error, job fires, no Discord message appears, no error recorded.

**Root cause:** The `deliver` field is processed by the **cron tool** (client-side), not the **scheduler** (server-side). The scheduler has no Discord delivery code path — it only has `web.deliver()` for internal session routing. `deliver: discord` is a valid config value but is never wired to any Discord API call.

**Evidence:** `grep -r "deliver\|discord" cron/scheduler.py` → zero matches for Discord delivery logic.

**Current state (May 2026):** Discord delivery from timer-fired jobs requires the **job prompt itself** to call `send_message` as a tool step. The scheduler's `deliver` field does NOT trigger Discord messages.

**Implication:** For jobs to reach Discord on schedule, the prompt must include a `send_message` call — not `deliver: discord`.

---

## The Diagnostic Pattern

```python
# Check if job has ever run
if job['last_run_at'] is None:
    print(f"⚠️  {name}: Never run — check schedule format, skill loading, script path")
    
# Check if delivery succeeded  
if job['last_delivery_error']:
    print(f"❌ {name}: Delivery failed — {job['last_delivery_error']}")

# Even with no error, check WHERE output went
if job['deliver'] == 'local':
    print(f"⚠️  {name}: deliver=local — output stored, not pushed to Sean")
```

---

## The Non-Negotiable Rule

```
IF a cron job's output is intended for human consumption:
  THEN "deliver: local" is NOT acceptable
  THEN delivery MUST be tested before scheduling
  THEN "last_status: ok" is NOT sufficient verification
  THEN verify: did Sean actually receive this?
```

**Test delivery in the same session that configures the job:**
1. Write the prompt
2. Force-run once immediately (`hermes cron run <job_id>`)
3. Verify output reaches the intended destination
4. Then enable the schedule

---

## Current Hermes Cron Jobs — Delivery Risk Assessment

| Job | Delivery | Risk |
|-----|----------|------|
| Night Owl Report | local | ❌ Never run |
| Memory Curation | local | ⚠️ Output not pushed |
| Morning Briefing | local | ❌ Never run |
| Cross-Agent Bridge Poll | local | ⚠️ Output not pushed |
| System Monitor & Cleaner | local | ⚠️ Output not pushed |
| HKUDS/ClawTeam Daily | local | ⚠️ Output not pushed |
| Delegation Monitor | local | ⚠️ Output not pushed |
| Autonomy Digest | local | ⚠️ Output not pushed |
| Infrastructure Daily | local | ⚠️ Output not pushed |
| Rate Smoother Backoff | local | ⚠️ Output not pushed |
| **Overnight Autonomy Engine** | local | ❌ Script path dead, false OK |
| Hermes Sync — GitHub Push | local | ❌ Never run |
| hermes-sync rolling rebuild | local | ❌ Never run |

**Pattern:** Every single job uses `deliver: local`. None push output to Sean directly.

---

## What Good Delivery Looks Like

For a morning briefing system:
- Output queued to a format Sean reads (email, Telegram, morning briefing aggregation)
- Critical findings (disk >95%, security issues, agent crashes) trigger immediate escalation
- Routine status goes into the daily digest

For an overnight engine:
- Summary of what was accomplished pushed to Sean's morning briefing
- Any blocking issues flagged immediately
- Full logs stored locally for debugging