# Session Search Query Reference for Auditors

These session_search query patterns are the fastest way to find audit evidence across sessions.

## Finding skill_view calls (C-001)
```
session_search(query="skill_view", limit=10, sort="newest")
```
Returns every session where skill_view was called. Each result includes the message_id of the call, bookend_start (first 3 messages of that session), and a ±5 message window around the match.

**Check**: Is the first tool call in the bookend_start a skill_view? If not, how far into the session was it?

## Finding file writes and edits (C-001 cross-reference)
```
session_search(query="write_file OR patch", limit=10, sort="newest")
```
Shows sessions where files were created or modified. Cross-reference with skill_view results to check ordering.

## Finding learning capture (C-003)
```
session_search(query="skill_manage OR memory", limit=10, sort="newest")
```
Shows sessions where skills were saved or memory was updated. Check the anchor message and bookend_end to see what was captured.

## Finding error-recovery patterns (C-003 trigger)
```
session_search(query="error OR fail OR timeout OR retry", limit=5, sort="newest")
```
Sessions where errors were overcome — these are candidates for C-003 violations if no learning was captured afterward.

## Browsing recent sessions (starting point)
```
session_search()  # no args — shows recent sessions
session_search(limit=20, sort="newest")  # more sessions
```

## Reading a session in detail
```
session_search(session_id="abc123", window=10)  # ±10 messages around a specific anchor
session_search(session_id="abc123")  # full session (first 20 + last 10)
```

## Key: `match_message_id`

Every discovery result includes `match_message_id`. Use this to scroll to the exact context:
```
session_search(session_id="abc123", around_message_id=12345, window=20)
```

This gives you 20 messages before + 20 after the match — enough to understand what was happening before and after the key event.

## Mental Model

Session search is a **retrieval tool**, not a ground-truth tool. Each result shows:
- `snippet`: the FTS5 match excerpt (may be truncated)
- `bookend_start`: first 3 assistant+user messages of that session (opportunity to see if skill_view was first)
- `bookend_end`: last 3 messages (opportunity to see if learning capture happened)
- `messages`: ±5 messages around the match (sufficient for most evidence checks)
- `match_message_id`: pointer for scrolling deeper

To verify a violation:
1. Discovery call → get session_id + match_message_id
2. Scroll call → get wider context around the event
3. If needed, scroll forward/backward using bookend_start/bookend_end boundaries
