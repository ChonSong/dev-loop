# Curator Config — Troubleshooting Reference

## Known Failure Mode: 404 on LLM Review Step

**Symptom:** Curator daemon logs show `HTTP 404: 404 page not found` during the LLM review pass. Daemon itself runs fine; only the review step fails.

**Root cause:** `provider: auto` in `auxiliary.curator` resolves to MiniMax-M2.7 at the provider level, but MiniMax rejects an empty `model` string for this particular API call pattern. The 404 is the HTTP response from the rejected request.

**Fix — edit `~/.hermes/config.yaml` around line 217:**
```yaml
auxiliary:
  curator:
    provider: openrouter   # was: auto
    model: anthropic/claude-sonnet-4   # was: ''
    timeout: 600
```

Any working LLM provider with a capable model works. The timeout of 600s is appropriate — the LLM review pass over the skill corpus can take several minutes.

## Verifying the Fix

After updating config, trigger a test run:
```bash
ssh sean@172.19.0.1 "cd /home/hermeswebui/.hermes && hermes config get auxiliary.curator"
```

Or check the daemon output for a successful LLM review pass (look for `evolver review complete` or similar in logs).

## Architecture Reminder

| What | Where |
|------|-------|
| Built-in curator daemon | `auxiliary.curator` in config.yaml |
| Curator skill (this skill) | `~/.hermes/skills/hermes-curator-evolver/SKILL.md` |
| Evidence SQLite | `~/.hermes/curator/evidence.db` |
| skill-selector | `~/.hermes/scripts/skill-selector.py` (independent, scores per turn) |
| skill-selector cache | `~/.hermes/skill-selector-cache/` |

Curator and skill-selector are independent systems. Curator can be broken and skill-selector still works fine. This reference is for when someone asks "why isn't curator improving skills" or "should we be using curator".