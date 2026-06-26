# MiniMax httpx 404 in Cron Jobs — May 2026

## Symptom

All 24 cron jobs using `provider: "custom"` fail with:
```
error_type=NotFoundError summary=HTTP 404: 404 page not found
```

The 404 response is HTML ("404 page not found"), NOT a JSON API error. Yet `curl` from the same container to `https://api.minimax.io/v1/chat/completions` returns HTTP 200 streaming.

**Critical diagnostic:** `"Creating OpenAI client"` log line appears for foreground sessions but **never** for cron sessions. Both reach the same `_create_openai_client` function. This log absence is primary evidence of a code path divergence.

## Relevant Files (Patched May 16, 2026)

| File | Change | Purpose |
|------|--------|---------|
| `cron/scheduler.py:1361-1377` | Added `[DEBUG]` prefix + api_key preview | Confirm which key is resolved |
| `run_agent.py:6612` | Added HERMES_PROXY env var logging | Detect proxy hijack in cron context |
| `cron/scheduler.py:1469` | Comment only | Documents HTML 404 interception hypothesis |

## Why curl works but httpx fails

Both use HTTPS to the same host. Possible causes:
1. httpx defaults to HTTP/2; API server/proxy handles it differently → fix: force HTTP/1.1
2. Proxy env vars set in cron context redirect httpx traffic
3. TLS version mismatch
4. SNI or host header differences

## API Key Discovery

`MINIMAX_API_KEY` (KEYA) and `MINIMAX_API_KEYB` (KEYB) are DIFFERENT keys (both 125 chars):
- KEYA (`sk-cp-...D0va`): Bearer token + `/v1/chat/completions`
- KEYB (`sk-cp-...zsvs`): X-Api-Key header + `/anthropic/v1/messages`

## Fix Direction

In `_build_keepalive_http_client` (`run_agent.py`), add explicit HTTP/1.1 mode for `api.minimax.io` base_url. Alternatively, add TLS configuration to bypass proxy for this endpoint.

## Verification

After fix, fire cron job and check `agent.log` for both:
```
[DEBUG] Job '4d2609ce31ba': resolved runtime — provider='custom' base_url='https://api.minimax.io/v1' key_preview='***D0va'
Creating OpenAI client
```

If `"Creating OpenAI client"` still absent → cron path is taking a different branch; investigate `_build_keepalive_http_client` code path directly.