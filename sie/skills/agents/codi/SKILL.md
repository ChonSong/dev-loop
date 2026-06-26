---
name: codi
description: Codi — code ingestion and refactoring agent. Specialized in understanding large codebases, refactoring, and code migration.
version: 1.0.0
author: migrated-from-openclaw
category: agents
metadata:
  openclaw_id: codi
  openclaw_name: "Codi – Code Ingestion & Refactoring"
---

# Codi – Code Ingestion & Refactoring
# Codi – Code Ingestion & Refactoring

Codi specializes in understanding, ingesting, and refactoring large codebases.

## Workspace

Codi's active workspace is `/workspace/codi/`. The workspace is self-contained with its own AGENTS.md, SOUL.md, IDENTITY.md, USER.md, HEARTBEAT.md, and CODE_INDEX.md. A `memory/` directory holds daily logs.

## Minimum Viable Workspace Setup

When provisioning a new codi workspace, all of these must be present:

| File/Dir | Purpose | Common Failure |
|----------|---------|----------------|
| `memory/` | Daily logs (`YYYY-MM-DD.md`) | Directory missing → no session continuity |
| `USER.md` | User profile (preferences, context) | Often blank template |
| `HEARTBEAT.md` | Periodic tasks (not just instructions) | Often empty, only has boilerplate |
| `CODE_INDEX.md` | Module inventory with accurate line counts | Line counts off by 10-30 lines; verify with `wc -l` |
| `AGENTS.md` | Routing hints (Codi = code ingestion) | Missing routing table alignment |
| `IDENTITY.md` | Agent identity | Must align with AGENTS.md description |

**Line count verification:** Always run `wc -l` on actual files to verify CODE_INDEX.md accuracy. Do not trust pre-filled counts.

## Tools
- read, write, exec, subagents

## Use case
When you need to understand a large codebase structure, refactor code, or migrate between frameworks, use codi.