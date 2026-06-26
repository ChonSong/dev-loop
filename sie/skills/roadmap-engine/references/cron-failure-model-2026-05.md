# Cron Job Failure Model — 2026-05-29

## Three-Tier Failure Classification

When a cron job fails, the error falls into exactly one of these categories:

### Tier 1: 400 "No models provided"

**Cause:** Job has `provider: null` or `provider: opencode-go` but the opencode-go provider has no API key in the container environment.

**Jobs affected (2026-05):**
- `d3aac3ef0953` (System Monitor & Cleaner) — provider: null

**Diagnosis:**
RuntimeError: Error code: 400 - {'error': {'message': 'No models provided', ...}}

**Fix:** Either fix the opencode-go provider OR switch the job's model to `openrouter/owl-alpha`.

### Tier 2: 402 "Insufficient credits"

**Cause:** Job resolves to the openrouter provider correctly, but the OpenRouter account is out of credits.

**Jobs affected (2026-05):**
- `4e516a10190d` (HKUDS/ClawTeam Daily Summary)
- `f53d0f3da390` (Delegation Monitor)
- `65d287b7c3c9` (Autonomy Digest)

**Diagnosis:**
RuntimeError: Error code: 402 - {'error': {'message': 'Insufficient credits...', ...}}

**Fix:** Add credits to OpenRouter account, OR switch to a provider that has credits.

### Tier 3: Stale filesystem paths

**Cause:** Job prompt hardcodes paths from the host perspective that don't exist in the container.

**Jobs affected (2026-05):**

| Job ID | Field | Stale Path | Real Path |
|---|---|---|---|
| `add0b41406ff` | WORKDIR | `/home/hermeswebui/.hermes/hermes-web-computer` | `/opt/data/hermes-web-computer` |
| `add0b41406ff` | STATE_DIR | `/home/hermeswebui/.hermes/hermes-web-computer-state/` | `/opt/data/hermes-web-computer-state/` |
| `ecb3846b907b` | workdir | `/home/hermeswebui/.hermes/hermes-web-computer` | `/opt/data/hermes-web-computer` |
| `b327d27d5798` | STATE_DIR | `/home/hermeswebui/.hermes/hermes-web-computer-state/` | `/opt/data/hermes-web-computer-state/` |

## Model/Provider Resolution in Container

Default model: `opencode-go/deepseek-v4-flash` — opencode-go has NO API key in the container. All jobs inheriting the default silently fail.

OpenRouter provider: configured with `${OPENROUTER_API_KEY}` from `/opt/data/home/.hermes/.env`.

To use OWL Alpha: set `model: openrouter/owl-alpha` on the cron job explicitly.

## Debug Steps for Any Failing Cron

1. Check output: `/opt/data/cron/output/<job-id>/latest.md`
2. Classify: 400=no model, 402=no credits, path=stale paths
3. Fix: update model/provider or fix the path reference
