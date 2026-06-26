# Hermes Session Failure Diagnosis

When a Hermes session "immediately fails" — prompts get no response, sessions are
unusable — the cause is rarely the prompt itself. Use this diagnostic sequence.

## Signal

- User says "my X session is broken / unusable / prompts immediately fail"
- Session hangs, times out, or errors on first message
- "this isn't the first time" — recurring pattern

## Phase 1: Profile Inventory

Check what profiles exist — the profile name in the user's complaint may not exist:

```bash
ls -la ~/.hermes/profiles/
# Each subdir = one profile with its own config.yaml, skills/, cron/, memories/
```

A missing profile means either: (a) it was never created, (b) it was deleted, or
(c) the user is referring to a session tab name, not a profile.

## Phase 2: State DB Health

The Hermes session database (`~/.hermes/state.db`) is the single source of truth
for all sessions. A bloated DB causes session load/save timeouts that manifest
as "immediately fails."

```bash
# Size check — >500MB is suspect, >1GB is critical
ls -lh ~/.hermes/state.db

# Session count by source (webui, cron, tui, discord, cli, api_server)
sqlite3 ~/.hermes/state.db 'SELECT source, COUNT(*) as cnt FROM sessions GROUP BY source;'

# Total messages
sqlite3 ~/.hermes/state.db 'SELECT source, SUM(message_count) as total_msgs FROM sessions GROUP BY source;'

# Recent sessions
sqlite3 ~/.hermes/state.db 'SELECT id, title, source, datetime(started_at, "unixepoch") FROM sessions ORDER BY started_at DESC LIMIT 10;'

# Sessions with errors
sqlite3 ~/.hermes/state.db 'SELECT id, title, source, datetime(started_at, "unixepoch"), end_reason FROM sessions WHERE end_reason = "error" ORDER BY started_at DESC LIMIT 20;'
```

**Thresholds** (from real data):
- 1.9GB state.db with 3,602 sessions and 157,729 messages = severe bloat
- 62K messages across 1,213 webui sessions = typical active-use accumulation
- 43K messages across 1,920 cron sessions = every cron tick adds a session
- Zombie `<defunct>` hermes processes = stale children not reaped

**Root causes of bloat:**
- `sessions.auto_prune: false` in config.yaml — sessions never auto-deleted
- Every cron job run creates a new session entry (1,920+ cron sessions is normal over months)
- Long sessions accumulate messages without bound
- No retention limit on session message count

## Phase 3: Process Check

Zombie processes indicate sessions that crashed without proper cleanup:

```bash
ps aux | grep hermes | grep defunct
# Count them:
ps aux | grep -c 'hermes.*defunct'
```

Multiple defunct processes can exhaust PID limits and prevent new session launches.

Also check if the gateway is alive:

```bash
hermes gateway status
ps aux | grep -i 'hermes gateway'
```

## Phase 4: Provider Config Verification

If the model provider isn't configured, API calls fail instantly:

```bash
# Check the configured model and provider
grep -A2 '^model:' ~/.hermes/config.yaml

# Check custom_providers for the referenced provider
grep -A2 'name:' ~/.hermes/config.yaml | grep -v '^\-\-'
```

**Pattern:** If the model stanza references a provider that isn't in
`custom_providers` or `providers`, and isn't a built-in Hermes provider, the
session will fail on every API call. The error may not surface as
"provider not found" — it shows as a silent timeout or immediate exit.

## Phase 5: Session Data Inspection

For a specific session ID, check its message count:

```bash
sqlite3 ~/.hermes/state.db "SELECT COUNT(*) FROM messages WHERE session_id = '<id>';"
```

A session with very few messages but a "stuck" appearance may have corrupted
message state. Compare against similar sessions from the same source.

## Remarks (root cause dependent)

- **DB bloat**: Enable `sessions.auto_prune: true` in config.yaml (set `retention_days: 90`). Run `VACUUM` after pruning.
- **Zombie processes**: Identify and kill parent process or clean up directly.
- **Missing provider**: Add the provider to `custom_providers` with correct `api_key`, `base_url`, and `api_mode`.
- **Corrupted session**: Delete the session from DB; client creates a new one.
