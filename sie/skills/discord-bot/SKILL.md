---
name: discord-bot
description: Post messages to Discord channels via REST API. Covers token management, message formatting, 2000-char split, webhook alternatives, and common pitfalls.
always: false
---

# Discord Bot

Post messages to Discord channels via the REST API. Used for cron-driven reports, notifications, and automated updates.

## Prerequisites

- Discord bot token (from `.env` or environment)
- Bot must be invited to the server and have `Send Messages` permission in the target channel

## Token Location

Discord bot tokens and channel IDs stored in:
- **Container/cron env**: `/opt/data/.env` (keys: `DISCORD_BOT_TOKEN`, `DISCORD_CHANNEL_ID`)
- **Host (EndeavourOS)**: `/home/sean/.hermes/.env`
- **Legacy container**: `/home/hermeswebui/.hermes/.env`

**Critical pitfall**: `read_file` masks secret values as `***`. Always extract tokens via `terminal` + `grep` or Python `subprocess.run`/direct file line parsing (see code below).

## Posting a Message

```python
import urllib.request, urllib.error, json

channel_id = '123456789012345678'  # target channel ID
dc_token = 'YOUR_BOT_TOKEN'       # from .env

discord_url = f'https://discord.com/api/v10/channels/{channel_id}/messages'
message = 'Your message content here (max 2000 chars)'

req = urllib.request.Request(
    discord_url,
    data=json.dumps({'content': message}).encode(),
    headers={
        'Authorization': f'Bot {dc_token}',
        'Content-Type': 'application/json',
        'User-Agent': 'Hermes-Bot'      # REQUIRED — Discord rejects requests without this
    },
    method='POST'
)
try:
    with urllib.request.urlopen(req, timeout=20) as resp:
        result = json.loads(resp.read())
        print(f"Posted! Message ID: {result.get('id')}")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"Error {e.code}: {body}")
```
```

## Message Length Limit — Split Strategy

Discord's content field is capped at **2000 characters**. For reports that exceed this, split into multiple messages:

```python
MAX_MSG = 2000

def post_discord(channel_id, token, content):
    """Post a single message. Returns success/failure."""
    url = f'https://discord.com/api/v10/channels/{channel_id}/messages'
    req = urllib.request.Request(
        url,
        data=json.dumps({'content': content}).encode(),
        headers={
            'Authorization': f'Bot {token}',
            'Content-Type': 'application/json',
            'User-Agent': 'Hermes-Bot'
        },
        method='POST'
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return True, json.loads(resp.read()).get('id')
    except urllib.error.HTTPError as e:
        return False, e.read().decode()[:200]

def post_split_messages(channel_id, token, sections):
    """Post multiple sections as separate messages, splitting if needed."""
    results = []
    for section_text in sections:
        if len(section_text) <= MAX_MSG:
            ok, info = post_discord(channel_id, token, section_text)
            results.append((ok, info))
        else:
            # Split on newlines, accumulating chunks
            lines = section_text.split('\n')
            chunk = ''
            for line in lines:
                if len(chunk) + len(line) + 1 > MAX_MSG:
                    if chunk:
                        ok, info = post_discord(channel_id, token, chunk)
                        results.append((ok, info))
                    chunk = line
                else:
                    chunk = (chunk + '\n' + line).strip()
            if chunk:
                ok, info = post_discord(channel_id, token, chunk)
                results.append((ok, info))
    return results
```

**Practical pattern**: Build logical sections (header, PRs, issues, CI), check each section's length, and post each as a separate message. This gives natural break points and avoids mid-sentence splits.

## Discord Markdown

Discord supports a subset of markdown:

| Format | Syntax |
|--------|--------|
| **Bold** | `**text**` |
| *Italic* | `*text*` or `_text_` |
| ~~Strikethrough~~ | `~~text~~` |
| `Inline code` | `` `code` `` |
| Code block | `` ```\ncode\n``` `` |
| [Link](url) | `[text](url)` |
| > Quote | `> text` |
| Underline | `__text__` |

**Important**: Discord does NOT support `:emoji:` shortcode syntax in bot messages. Use actual Unicode emoji characters (🔴🟢✅❌📋⚙️) instead. However, custom server emojis can be referenced as `<:name:id>`.

The `:red_circle:`, `:green_circle:`, etc. shortcodes shown in Discord UI **do work** in bot messages — Discord resolves them server-side. But standard Unicode is safer for cross-compatibility.

## Embeds (Rich Messages)

Embeds provide rich formatting (color bars, fields, footers) but consume more token space:

```python
embed = {
    'embeds': [{
        'title': 'Daily Report',
        'description': 'Summary text here',
        'color': 0x00ff00,  # green
        'fields': [
            {'name': 'Open PRs', 'value': '5', 'inline': True},
            {'name': 'Merged', 'value': '3', 'inline': True},
        ],
        'footer': {'text': 'Generated by Hermes'}
    }]
}

req = urllib.request.Request(
    url,
    data=json.dumps(embed).encode(),
    headers={
        'Authorization': f'Bot {dc_token}',
        'Content-Type': 'application/json',
    },
    method='POST'
)
```

Note: Embeds have a 6000-character total limit (separate from the 2000-char content limit). A message can have both `content` and `embeds`.

## Webhooks (No Bot Required)

If you don't need a bot user (just posting to a channel), webhooks are simpler:

```python
webhook_url = 'https://discord.com/api/webhooks/WEBHOOK_ID/WEBHOOK_TOKEN'
req = urllib.request.Request(
    webhook_url,
    data=json.dumps({'content': 'Hello from webhook!'}).encode(),
    headers={'Content-Type': 'application/json'},
    method='POST'
)
```

Create a webhook: Channel Settings → Integrations → Webhooks → New Webhook → Copy URL.

## Error Codes

| Code | Meaning |
|------|---------|
| 400 | Invalid Form Body — content too long (>2000), bad JSON, invalid embed |
| 401 | Unauthorized — bad token, bot not in server |
| 403 | Missing Access — bot lacks permission in channel **OR** Cloudflare proxy in front of Discord API returns 403 for auth failures. Discord's own auth failure (bad token) also returns 403 — use `User-Agent: Hermes-Bot` header to distinguish. If 403 persists with valid token, Cloudflare may be rate-limiting; check `Retry-After` header. |
| 404 | Unknown Channel — wrong channel ID |
| 429 | Rate Limited — back off, check `Retry-After` header |

## Token Extraction

Extract tokens safely — `read_file` masks secrets as `***`, so use `grep` via `terminal` or Python line-parsing:

```python
# Python — line-by-line parsing (handles '=' in token values correctly)
with open("/opt/data/.env") as f:
    for line in f:
        if line.startswith("DISCORD_BOT_TOKEN="):
            token = line.rstrip().split("=", 1)[1]
        elif line.startswith("DISCORD_CHANNEL_ID="):
            channel = line.rstrip().split("=", 1)[1]
```

**Why line-parsing over `split('DISCORD_BOT_TOKEN=')[1]`**: Token values can contain `=` characters. Splitting on the full key prefix with `maxsplit=1` is safe; splitting naively on just `=` picks the wrong boundary.

**`execute_code` vs `terminal` for cron scripts**: `terminal` can inherit a broken CWD in container envs, producing `cd: /opt/data: No such file` errors. Python file reads or `subprocess.run` with explicit paths avoid this entirely.

## Unresponsive Bot — Quick Fix

If the bot receives messages but silently drops them (no response, no error):

1. **Try `/stop`** in the Discord thread — clears the session from `_running_agents` (releases the running state lock). This is more effective than `/reset` which only invalidates the generation.
2. **If `/stop` doesn't work, `/reset`** — clears stale session state
3. **If both fail, `/restart`** — full gateway reconnect (disruptive but clears all state)
4. **See `references/discord-unresponsive-debug.md`** for full diagnostic flow (general case)
5. **See `references/discord-session-lock.md`** for the specific case where a long-running session holds `_running_agents` and silently drops messages — `/stop` is the fix, not `/reset`

## Pitfalls

1. **Session lock causing silent drops**: When `_busy_input_mode: "interrupt"` (the default), a message arriving while a non-ephemeral session holds `_running_agents` is silently dropped — no response, no error, not even queued. `/stop` releases the lock; `/reset` does NOT.
2. **`/reset` vs `/stop`**: `/reset` calls `_interrupt_and_clear_session(release_running_state=False)` — it only invalidates the generation. The session can re-enter `_running_agents` during text batch flush. `/stop` calls `_interrupt_and_clear_session(release_running_state=True)` — removes the session from `_running_agents` entirely. For Discord thread hangs, `/stop` is the correct tool.
**Discord bot silently drops messages — no response, no error, no ACK:**

The symptom: messages arrive at the gateway (`inbound message` logged), the session lock is cleared via `/stop`, but the message still produces no response. This happens when `busy_input_mode: "interrupt"` (default) and messages arrive during the session cleanup transition window.

**Root cause:** When `_interrupt_and_clear_session()` fires (line ~13820), it calls `get_pending_message()` which consumes and discards the text batch queue. If a new message arrives during this brief window (between when the old session's lock is released and before the new session is fully claimed), the message enters `_pending_text_batches` but immediately gets consumed by the in-progress cleanup — silently, with no response delivered.

**Fix — change `busy_input_mode` in `config.yaml`:**
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

**See `references/discord-session-lock.md`** for the older failure mode (long-running session holding `_running_agents` for 25+ min).

2. **Thread not in `allowed_channels`**: If a Discord thread is not in `config.yaml`'s `allowed_channels` list, the bot relies on `ThreadParticipationTracker` + `require_mention: false`. The thread should be in `discord_threads.json` (auto-tracked on first response) but adding it to `allowed_channels` explicitly guarantees responsiveness.

## See Also

- **Voice channels** → `discord-voice` skill covers full-duplex voice conversation: join/leave VC, STT transcription, TTS responses, `/voice` slash commands, VoiceReceiver pipeline, and wake word integration.
