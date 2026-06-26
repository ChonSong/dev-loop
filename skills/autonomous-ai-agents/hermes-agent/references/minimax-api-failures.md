# MiniMax API Failure Modes — hermes-agent

**Source:** Session 2026-05-08 cron job analysis  
**Date:** 2026-05-08

---

## MiniMax at api.minimax.io/anthropic

The MiniMax provider is configured as:
```yaml
model:
  base_url: https://api.minimax.io/anthropic
  default: minimax/MiniMax-M2.7
  provider: minimax
```

This base URL accepts OpenAI-format requests (`/v1/chat/completions`) but the MiniMax **does NOT support the Claude SDK endpoints** that hermes-agent uses internally for:
- Session summarization (`session_search` tool)
- Title generation
- Context compression prompts

---

## Failure Mode: Model Error 1211

```
openai.BadRequestError: Error code: 400 - {'error': {'code': '1211', 'message': 'Unknown Model, please check the model code.'}}
```

**Trigger:** hermes-agent calls `async_call_llm` with `model="MiniMax-M2.7"` against the MiniMax API for auxiliary tasks (summarization, title generation).

**Root cause:** The MiniMax API `/v1/chat/completions` endpoint doesn't recognize `MiniMax-M2.7` as a valid model ID — it only accepts models in the MiniMax catalog. The base URL at `api.minimax.io/anthropic` is meant for Claude-format requests but the hermes runtime is sending OpenAI-format auxiliary requests.

**Symptom in cron jobs:** `"Agent completed but produced empty response (model error, timeout, or misconfiguration)"` — the agent actually ran and produced output, but the post-processing step (summarization or title generation) failed, making the final deliverable empty.

**Affected cron jobs (2026-05-08):**
- Morning Briefing — `last_status: error`
- System Monitor & Cleaner — `last_status: error`
- Autonomy Digest — `last_status: error`
- HKUDS/ClawTeam Daily Summary — `last_status: error`

**NOT affected (no summarization call):**
- hermes-sync rolling rebuild — `last_status: ok`
- Delegation Monitor — `last_status: ok`
- Cross-Agent Bridge Poll — `last_status: ok`

---

## Detection

```python
# Check agent.log for model 1211 errors:
grep "1211" ~/.hermes/logs/agent.log
grep "Unknown Model" ~/.hermes/logs/agent.log
grep "Session summarization failed" ~/.hermes/logs/agent.log
grep "Title generation failed" ~/.hermes/logs/agent.log
```

---

## Workarounds

### Option 1: Disable summarization/title generation
Set in `~/.hermes/config.yaml`:
```yaml
compression:
  enabled: false
session_search:
  enabled: false
```
Then `/reset` for changes to take effect.

### Option 2: Use a fallback provider for auxiliary tasks
The `auxiliary` section in config.yaml can override the provider for specific tasks:
```yaml
auxiliary:
  compression:
    provider: openrouter
    model: anthropic/claude-3-haiku
  vision:
    provider: minimax
    model: MiniMax-M2.7
```

### Option 3: Use a different model for the main provider
Switch from `minimax/MiniMax-M2.7` to a model whose API properly handles all hermes-agent internal calls. This is the cleanest fix if MiniMax billing or context length is not critical.

---

## The Empty Response Diagnosis Path

When a cron job fails with "empty response":

1. Check `~/.hermes/logs/agent.log` for model errors (`1211`, `400`, `Unknown Model`)
2. If found → it's the MiniMax summarization/title generation failure, not a prompt or tool failure
3. The agent DID run successfully; the failure is in post-processing
4. Fix per above workarounds

This is distinct from delivery failures (output produced but not received) and from script-path failures (job never runs).
