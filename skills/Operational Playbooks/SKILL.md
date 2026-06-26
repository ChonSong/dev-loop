---
name: Operational Playbooks
description: Practical Hermes operational patterns — memory system quirks, Discord token maintenance, cron management, SSH host access setup, and other day-to-day operations.
category: devops
tags:
  - hermes
  - operations
  - maintenance
  - troubleshooting
---

# Operational Playbooks

Practical workflow patterns for Hermes production operations.

## When to Load

- Memory tool refuses writes due to drift guard
- Discord connection failing with 401 "Improper token"
- Setting up or repairing SSH host access from container
- Managing cron jobs, log rotation, or stale service cleanup
- Any "how do I fix this operational issue" question about Hermes itself

## Skills structure

This skill provides reference files for specific operational patterns:

| Reference | When |
|-----------|------|
| `references/memory-drift-guard.md` | Memory tool refuses writes — file format mismatch |
| `references/discord-token-refresh.md` | Discord 401 errors, invalid token, gateway restart |
