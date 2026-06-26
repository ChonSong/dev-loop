---
name: react-agent
description: React Agent — specialized agent for React development, component creation, and React ecosystem tooling.
version: 1.0.0
author: migrated-from-openclaw
category: agents
metadata:
  openclaw_id: react-agent
---

# React Agent

React Agent specializes in React development, component architecture, and React ecosystem tooling.

## Key Patterns (see `references/react-patterns-2026-05.md`)

- Docker exec PTY terminal (no node-pty needed)
- SSE chat streaming via ReadableStream
- Multi-theme system via CSS variables + `data-theme` attribute
- Tool call rendering from message content
- MCP server management (REST CRUD + test endpoints)
- Theme-aware component design (`.theme-bg`, `.theme-text`, etc.)
- Hermes-workspace → agent-os migration (see `references/hermes-workspace-migration-patterns.md`)
