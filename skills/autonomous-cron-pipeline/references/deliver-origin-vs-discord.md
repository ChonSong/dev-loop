# Deliver Parameter — origin vs discord vs all

## The Problem

Multiple cron jobs were failing silently. Results never appeared anywhere — not in Discord, not in the chat. Investigation revealed the delivery target was misconfigured.

## What Was Tested (May 15, 2026)

| deliver value | Behavior | Result |
|---------------|----------|--------|
| `discord` | Routes to `DISCORD_CHANNEL_ID` from `.env` | Silently fails — channel not connected |
| `all` | Attempts to resolve multiple targets | **Scheduler error**: "no delivery target resolved for deliver=all" |
| `local` | Saves to local output only | Works, but user doesn't see results |
| `origin` | Delivers to current chat | **WORKS** — reliably appears in the active chat |

## Root Cause

`deliver: discord` resolves to `DISCORD_CHANNEL_ID` but that channel (1486919044757061652) is not wired as a delivery destination in the scheduler's context. The scheduler accepts the value without error, but the actual post never reaches a channel the user monitors.

`deliver: all` is not a supported value — the scheduler throws "no delivery target resolved".

## Correct Pattern

Always use `deliver: "origin"` for results that should appear in the current chat.

If you need Discord AND origin delivery:
1. Set `deliver: "origin"` on the cron job
2. After completion, POST to Discord manually using the bot token

Manual Discord POST (Python):
```python
import urllib.request, json
token = 'MTQ4NjkxMjkxNzAyMTUyODE5NQ.GZCI0x...'  # DISCORD_BOT_TOKEN from ~/.hermes/.env
channel = '1486919044757061652'  # DISCORD_CHANNEL_ID from ~/.hermes/.env
req = urllib.request.Request(
    f'https://discord.com/api/v10/channels/{channel}/messages',
    data=json.dumps({'content': 'Results here'}).encode(),
    headers={'Authorization': f'Bot {token}', 'Content-Type': 'application/json'},
    method='POST'
)
with urllib.request.urlopen(req, timeout=20) as r:
    print("Posted:", json.loads(r.read()).get('id'))
```

## The 401 vs Delivery Distinction

A cron job failing with `last_status: error` and 401 is NOT a delivery problem — it's an authentication problem. The job never got to the delivery stage because the model call failed first.

Symptoms:
- `last_status: error` with "login fail: Please carry the API secret key" → auth failure (fix: use `provider: "custom"`)
- `last_status: error` with "no delivery target resolved" → deliver value not supported
- `last_status: error` with no error visible → likely auth + silently skipped delivery

## Jobs Fixed in This Session

- f5a499e5d25a (HWC Phase Engine) — disappeared after repeat exhausted, recreated as 85d63c9f073a
- 4d2609ce31ba (agent-os-canary-watch) — minimax-portal → custom
- 56685e569e5f (Morning Briefing) — minimax-portal → custom
- 6d747879c7c5 (Cross-Agent Bridge Poll) — minimax-portal → custom
- 33ee3807d679 (hermes-sync rolling rebuild) — minimax-portal → custom, deliver → origin
- 2c60270a3745 (Hermes Full Backup git) — minimax-portal → custom
- ad90af79146c (Hermes Full Backup docker) — minimax-portal → custom

All now use `provider: "custom"` and `deliver: "origin"`.