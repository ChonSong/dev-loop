---
name: claude-design
description: Design one-off HTML artifacts (landing, deck, prototype) — process, taste, and verification standards for CLI/API agents. The canonical version lives at `creative/claude-design`.
category: creative
tags: [design, html, prototype, ux, ui, creative, artifact, deck, motion, design-system]
source: local
---

# claude-design

Design one-off HTML artifacts (landing, deck, prototype).

**Category:** creative

For the full skill content (rich SKILL.md with design process, anti-slop rules, deck rules, pitfall catalog, artifact guidance), use `skill_view(name='creative/claude-design')` to load the canonical version.

This root-level entry exists as an import point. The canonical skill with all procedural content lives under `skills/creative/claude-design/`.

## Key Pitfall Added in 2026-06-06 Session

- **Verify rendered output, not just source files, after subagent-driven redesign:** A subagent that "updated all files" can still produce a broken page — wrong CSS variable references, missing imports, zombie components that don't re-render, or components that render empty output. After the subagent finishes and type checks pass, build the frontend, restart the server (killing any zombie processes first), and curl the actual page body for expected content strings. If the rendered page shows empty divs, default text, or the old content, iterate with specific fixes rather than re-delegating wholesale.

- **Port-holding zombie trap:** A dead server can leave a zombie process holding the port. Next.js doesn't force-kill old servers on startup. After rebuilding, always verify the running server is the NEW build by checking the build ID or response body size. Kill all matching processes by PID before restarting.
