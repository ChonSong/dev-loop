---
name: context-recall
description: "Systematic search of past context when user references something from a previous session: multi-query session_search, memory check, file search, synthesis."
category: software-development
tags: [recall, memory, session-search, cross-session, retrieval]
---

# Context Recall — Finding Past Information Across Sessions

## When to Use

The user asks you to recall something you discussed before:
- "Remember when we talked about X?"
- "Recall our philosophy/approach for Y"
- "What did we decide about Z?"
- "Bring back that concept we discussed"
- "Look at our other session for context"

This covers the case where the user references a past conversation, decision, or concept that you don't have in your current context.

## Systematic Recall Protocol

Do NOT rely on a single search. The user's phrasing may not match the exact words used in the original session. Run multiple passes.

### Pass 1: Direct Query (session_search)

Start with the exact phrase the user used:

```
session_search(query="exact phrase", limit=5)
```

If the phrase is long or specific, try shorter versions after.

### Pass 2: Expand Query Vocabulary

If Pass 1 returns nothing useful, expand to synonyms and related concepts. The user may be paraphrasing. Try:
- Keywords from the topic area (e.g., "philosophy", "ethos", "principle", "approach")
- Related tool names, project names, skill names
- Broad terms the original conversation might have used

Multi-word queries: `AND` is the default in FTS5. Use `OR` for broader recall. Use quoted phrases for exact matches.

### Pass 3: Browse Recent Sessions

If queries fail, get a chronological view:

```
session_search()  # no args = browse mode
```

Look through recent session titles and previews for anything that matches the topic. If you spot a candidate:

```
session_search(session_id="...")  # read the full session
```

### Pass 4: Check Persistent Memory

```
memory(action="add"...) — no, check the drift issue
```

Read the MEMORY.md and USER.md content from your system prompt (they're injected into every turn). If they contain relevant entries, use them. If the memory tool reports drift, check the drift backup:

The memory section in your system prompt is the primary source — read it first before trying the memory tool, since drift can prevent reads.

### Pass 5: File Search (last resort)

If the concept might be documented in a file (AGENTS.md, SPEC.md, project documentation, archived notes):

```
search_files(pattern="keyword", target="content", path="/path/to/likely/location", limit=20)
```

Focus on:
- Project root directories (e.g., `/home/sc/repos/...`)
- The workspace
- Archived documentation directories

### Pass 6: Synthesize

When you can't find the exact phrasing but have gathered enough fragments, be honest about what you found and what you're inferring:

> "I can't find a specific document called 'our philosophy for the future.' Based on what I gathered from [X] sessions and [Y] files, here's what I know: [synthesize]. If you meant something else, give me another angle."

Do NOT fabricate a document or conversation that doesn't exist. Acknowledging gaps is better than hallucinating.

## Pitfalls

- **Memory drift**: The MEMORY.md file can get out of sync with the memory tool if it was edited externally. Check the system prompt's memory section first (it's always injected fresh each turn).
- **Session DB retention**: session_search only covers recent sessions — older ones may be evicted. If `count: 0` comes back, the session may be gone entirely.
- **User paraphrases**: The user's phrasing today may not match the original words. Be flexible with query terms.
- **False confidence**: session_search with `count: 0` is definitive — there's no session match. Don't claim "I recall we discussed..." unless you actually found it.
- **Multiple passes**: One failed query is not enough data to conclude "not found." Run at least 3 different query strategies before giving up.
