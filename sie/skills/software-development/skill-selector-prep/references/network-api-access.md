# Skill Selector — Network & API Access

## Container Network Isolation

**The container has no outbound internet access.** `api.openrouter.ai`, `api.minimax.io`, and all LLM provider endpoints are unreachable from inside the container. DNS resolution fails with `Name or service not known`.

Workaround: SSH to host (`sean@172.19.0.1`) and run API calls from there.

## OpenRouter Credits Exhausted

**API key `sk-or-v1-...` has zero credits.** Both `openrouter/free` and `openrouter/auto` return HTTP 402.

Affected operations:
- LLM tiebreaker in `skill-selector.py` (borderline scoring)
- Batch summarization of 986 unsummarized skills

## Available Workarounds

### 1. Host as jump box (current)
Run API calls via SSH to the host machine which has internet access:
```bash
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 \
  'curl -s "https://api.openrouter.ai/api/v1/chat/completions" \
   -H "Authorization: Bearer $OPENROUTER_API_KEY" ...'
```
Limitation: OpenRouter credits are still exhausted.

### 2. Switch to MiniMax API
MiniMax is the active provider (MiniMax-M2.7 model). Its API key should be functional.
- Need to confirm MiniMax chat API endpoint and request format
- MiniMax-Text-01 or abab6.5s-chat are candidates
- Key stored in `~/.hermes/.env` as `MINIMAX_API_KEY`

### 3. Add OpenRouter credits
Go to https://openrouter.ai/settings/credits and add funds. ~$5-10 is sufficient for batch summarization of ~1,400 skills at ~50 batches × 20 skills × low token count.

## Skill-Selector Script Locations

```
/home/hermeswebui/.hermes/skill-selector-cache/
  skill_metadata.json     — 1,441 skills (name, category, description, tags, size_mb, source)
  skill_summaries.json   — 453 LLM summaries (want: 1,441)
  context_scores.json    — pre-scored per workspace
  batches.json           — 50 batches × 20 skills (for batch summarization)

/home/hermeswebui/.hermes/scripts/
  skill-selector.py              — every-turn scorer
  skill-selector-prep.py         — weekly cache builder
  generate-skill-summaries.py     — LLM batch summarizer (poolside model)
  summarize-remaining.py         — NEW: streaming summarizer (not yet working)
```

## Batch Summarization Strategy

The `batches.json` file contains 50 batches (20 skills each = 1,000 skills). To complete:
1. Run subagent with SSH access to host + MiniMax API key
2. Or: run from host directly with a working API
3. Or: add OpenRouter credits

The batch index:
- Batches 0-16 (341 skills): attempted, all 402 errors
- Batches 17-49 (605 skills): not attempted

## Summary Coverage (2026-05-25)

| Source | Skills | Summarized | Remaining |
|--------|--------|------------|-----------|
| voltagent | ~1,117 | ~200 | ~917 |
| local | 153 | 153 | 0 |
| 0xNyk | ~135 | ~30 | ~105 |
| mattpocock-skills | 28 | 28 | 0 |
| vercel-labs-skills | 4 | 2 | 2 |
| expo-skills | 4 | 2 | 2 |
| **Total** | **~1,441** | **~453** | **~988** |

Local skills (153) are fully summarized. Remote skills from voltagent/0xNyk are the gap.