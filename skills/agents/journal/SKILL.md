---
name: journal
description: Journal — Notion logging agent. Records daily logs, journals, and notes into Notion.
version: 1.0.0
author: migrated-from-openclaw
category: agents
metadata:
  openclaw_id: journal
  openclaw_name: "Journal Agent – Notion Logging"
  model:
    primary: stepfun/step-3.5-flash:free
    fallbacks:
      - minimax/MiniMax-M2.5
---

# Journal – Notion Logging

Journal records daily logs, journals, and notes into Notion.

## Tools
- read, skill (limited)
- Denied: exec, sessions_spawn, browser, subagents, write

## Use case
Daily journaling, logging work sessions, and maintaining a personal knowledge log in Notion.
