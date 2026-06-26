# MiniMax httpx 404 in Cron Context — Debug Log Investigation

**Symptom:** All cron jobs using `provider: "custom"` (MiniMax-M2.7) fail with:
```
error_type=NotFoundError summary=HTTP 404: 404 page not found
```
The HTML body "404 page not found" confirms an HTTP-level 404, not a JSON API error. Yet `curl` from the same container to the same `https://api.minimax.io/v1/chat/completions` succeeds with 200.

**Key diagnostic finding (May 16, 2026):**

The log line `"Creating OpenAI client"` appears in `agent.log` for foreground sessions but **never for cron sessions** — even though both paths should reach the same `_create_openai_client` function in `run_agent.py`.

Foreground (works): `Creating OpenAI client (agent_init, shared=True) thread=... provider=custom base_url=https://token-plan.ap-southeast...`
Cron (broken): `"Creating OpenAI client"` line **absent** from agent.log entirely.

This absence is the primary diagnostic signal. It indicates the cron path is either:
1. Taking a different code path that doesn't log at INFO level, OR
2. The logging level in cron sessions filters out INFO-level lines

**Investigation steps applied:**

1. **Patched `_resolve_explicit_runtime`** (scheduler.py) to add `[DEBUG]` prefix to the runtime resolution log and include `key_preview` (last 4 chars of api_key masked). This shows which MINIMAX API key is being resolved — KEYA (`sk-cp-...D0va`) vs KEYB (`sk-cp-...zsvs`).

2. **Patched `_create_openai_client`** (run_agent.py line 6613) to log `HERMES_PROXY` env var status before client creation. This targets the hypothesis that a proxy env var redirects httpx traffic in cron context only.

3. **Verified curl works** — streaming 200 OK from the same container to `api.minimax.io/v1/chat/completions` using Bearer token from `.env`.

4. **Verified KEYA vs KEYB** — `MINIMAX_API_KEY` (125 chars, starts `sk-cp-...D0va`) and `MINIMAX_API_KEYB` (125 chars, starts `sk-cp-...zsvs`) are DIFFERENT keys. Both need to be tested with `/anthropic/v1/messages` and `/v1/chat/completions` paths respectively.

**Current status (patch applied, awaiting verification run):**

Two patches applied to source code:
- `cron/scheduler.py` lines 1361-1377: debug logging with api_key preview
- `run_agent.py` line 6612: `HERMES_PROXY` env var logging before httpx client creation

Next step: fire a fresh cron job and grep `agent.log` for:
- `[DEBUG] Job resolved runtime — provider=... base_url=... key_preview=...`
- `Creating OpenAI client`
- `HERMES_PROXY` env status

If `Creating OpenAI client` still absent after the patches, the code path difference is confirmed and the investigation must focus on `_build_keepalive_http_client` TLS/HTTP2 negotiation.

**Related files:**
- `hermes-agent/references/cron-delivery-failures.md` — cron delivery failure taxonomy (delivery not logging)
- `hermes-agent/SKILL.md` § Cron CLI fails with exit code 2 — `cronjob run` HTTP 404 is a separate issue (missing endpoint, not httpx routing)