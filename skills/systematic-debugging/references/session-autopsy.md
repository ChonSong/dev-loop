# Session Autopsy: Analyzing Hermes Session Death Patterns

When a user says "my session is broken" or "prompts immediately fail," the session itself may hold the diagnostic evidence — even when the DB is the ultimate bottleneck.

## The Diagnostic Triad

Three measurements reveal how a session died:

### 1. Message Ratio (User : Assistant)

```sql
SELECT role, COUNT(*) as cnt
FROM messages WHERE session_id = '<sid>'
GROUP BY role;
```

| Ratio | Interpretation |
|-------|---------------|
| **1:3 to 1:5** | Normal productivity. Each user query generates a few assistant+tool rounds. |
| **1:8 to 1:12** | High verbosity. Model is retrying, debugging, or iterating on failed tool calls. Each user message generates 8+ assistant rounds. |
| **1:15+** | Death spiral. Model is stuck in a loop — likely repeated failures of the same tool (vision, web_search, etc.), debug attempts that don't resolve, or context compression thrashing. |

**Real-world example:** A 451-message session with 23 user messages = **1:11 ratio**. The model tried `vision_analyze` repeatedly without a configured vision API key. Each attempt failed → the model debugged → failed again → generated 25+ retries before the user gave up.

### 2. Lifespan / Message Density

```sql
SELECT datetime(MIN(timestamp), 'unixepoch') as first,
       datetime(MAX(timestamp), 'unixepoch') as last,
       ROUND((MAX(timestamp)-MIN(timestamp))/3600.0, 1) as hours_span,
       COUNT(*) as total_msgs,
       ROUND(COUNT(*) / (MAX(timestamp)-MIN(timestamp)+1) * 3600.0, 1) as msgs_per_hour
FROM messages WHERE session_id = '<sid>';
```

- **>50 msgs/hour** = rapid back-and-forth, likely active user engagement
- **5-50 msgs/hour** = normal paced conversation with tool calls
- **<5 msgs/hour** = low density, extended gaps between messages — the user was waiting for responses or had abandoned the session

A sudden drop in message density at the end of the session usually marks the abandonment point.

### 3. Failure Mode (Last 10 Messages)

```sql
SELECT role, substr(content, 1, 200) as preview, id
FROM messages WHERE session_id = '<sid>'
ORDER BY id DESC LIMIT 10;
```

**Common failure patterns:**

| Pattern | Evidence | Root Cause |
|---------|----------|------------|
| **Vision death spiral** | Repeated `vision_analyze` calls with errors like `File name too long`, `Errno 36`, missing API key | Auxiliary vision provider not configured (no API key, wrong base_url) |
| **Web search loop** | `Tool 'web_search' does not exist` repeated 3+ times | Model lacking web_search tool in its toolset; falls back to curl which gets bot-blocked |
| **Context exhaustion** | Compression messages, then silent failure | Context window exceeded; compression failed due to DB I/O timeout |
| **Provider auth failure** | `401` or `403` error messages | Provider API key missing, expired, or revoked |
| **Model routing error** | `400` with "model not found" or routing error | Stale model name, provider change, or config mismatch |
| **Silent DB death** | No error messages — just empty responses, or the session never loads | DB too bloated to read/write (1.9GB+ state.db at 95%+ disk) |

## The Death Spiral Cascade

Most session failures follow this sequence:

```
User message → Model attempts tool → Tool fails (config/network/DB)
           → Model retries with different parameters → Tool fails again
           → Model switches strategy (e.g., curl instead of web_search)
           → New strategy also fails (bot blocked, wrong endpoint)
           → Model enters debug loop (dump config, check env, try alternatives)
           → Session message count balloons (10+ assistant turns per user query)
           → Context window fills → Compression tries to save → Compression times out
           → DB write fails (disk full, slow DB) → Next user message can't be saved
           → Session completely unresponsive
```

**Key insight:** The *primary* failure (e.g., no API key) causes the *secondary* failure (swollen context → DB timeout). Fixing the primary prevents the cascade.

## Using This for Prevention

After any troubled session, check:

1. **Was the session fixable by a config change?** (API key, provider URL, toolset)
2. **Was the session fixable by a DB operation?** (prune, VACUUM, auto_prune enable)
3. **Was the session a victim of a known bug?** (tab leak, session_lifecycle.py memory leak, offline-reload loop)
4. **Was the session structurally doomed?** (11:1 assistant:user ratio → would have hit context limits no matter what)

If (4), check if `sessions.auto_prune: true` is set. If it's `false`, that's the root cause — session never gets compressed, never gets cleaned, DB grows until everything fails.
