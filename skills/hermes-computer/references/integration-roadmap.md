# Integration Roadmap: Best-of-All-Worlds Agent-OS

The goal: all valuable features from `nesquena/hermes-webui` + `hermes-workspace` + `agent-os` + `hermes-web-computer`, unified in one Go+Svelte5 codebase.

**Master plan lives at:** `/opt/data/hermes-web-computer/docs/ROADMAP.md`

---

## Source of Truth for Each Feature

| Feature | Source | Why |
|---------|--------|-----|
| Sessions (CRUD, FTS, projects, tags, CLI bridge) | `nesquena/hermes-webui` | Proven, 5303 tests |
| Streaming SSE, tool/approval cards | `nesquena/hermes-webui` | Production-hardened |
| Profiles, skills, cron, memory | `nesquena/hermes-webui` | Full implementation |
| Slash commands, themes (7), auth | `nesquena/hermes-webui` | Complete |
| Tiling WM, keyboard shortcuts | `hermes-web-computer` | Unique to HWC |
| Go backend, WS multiplexer | `hermes-web-computer` | Core architecture |
| Docker/container management | `agent-os` | Unique to agent-os |
| Observability, MCP management | `agent-os` | Unique to agent-os |
| Electron desktop shell | `hermes-workspace` (outsourc-e) | External, not forkable |

---

## What NOT to Take

| Source | What to Skip |
|--------|-------------|
| `hermes-workspace` | 3D environment, Swarm mode — too specific |
| `agent-os` | Postgres dependency (HWC uses SQLite) |
| `nesquena/hermes-webui` | Python server (we're Go), vanilla JS (we're Svelte5) |

---

## 6-Phase Implementation Order

```
Phase 1 (Weeks 1-2): Sessions + Chat + Streaming
  → hermes-webui parity: sessions, chat, profiles, skills, cron, memory
  → New: backend/session/store.go (SQLite), frontend SessionList.svelte

Phase 2 (Weeks 3-4): Tiling WM + Keyboard Shortcuts
  → Merge hermes-web-computer tiling into session UI
  → Shift+Space, Shift+Arrow, Ctrl+K command palette

Phase 3 (Weeks 5-6): Docker/Observability + Config
  → agent-os Docker/container management in Go+Svelte5
  → Real telemetry from ring buffer

Phase 4 (Weeks 7-8): Command Palette + MCP + Voice
  → Global Ctrl+K, MCP adapter, Fun-Audio-Chat relay

Phase 5 (Weeks 9-10): Electron Shell
  → Desktop app wrapping web UI (system tray, notifications)

Phase 6 (ongoing): Polish + Tests + CI/CD
  → Playwright E2E, Go tests, GitHub Actions
```

---

## Key Files to Study Before Each Phase

### Phase 1 — Session Architecture Reference
```bash
# Clone hermes-webui for reference (already cloned at /tmp/hermes-webui)
# Key files:
/tmp/hermes-webui/api/models.py          # Session model + in-memory store
/tmp/hermes-webui/api/streaming.py        # SSE engine + token streaming
/tmp/hermes-webui/api/routes.py           # All HTTP handlers (~9772 lines)
/tmp/hermes-webui/static/sessions.js      # Frontend session UI
/tmp/hermes-webui/static/panels.js        # Cron, skills, memory, profiles
```

### Phase 2 — Keyboard/Layout Reference
```bash
# hermes-web-computer already has:
/opt/data/hermes-web-computer/backend/layout/tree.go  # Binary tree layout
/opt/data/hermes-web-computer/PLAN.md                 # Three-column layout plan
/opt/data/hermes-web-computer/SPEC.md                 # Architecture spec (v2.0)
```

### Phase 3 — Docker/Observability Reference
```bash
# agent-os has working Dockerode integration:
/opt/data/agent-os/apps/dashboard/backend/src/index.ts  # Express routes for containers
/opt/data/agent-os/apps/dashboard/frontend/src/pages/DockerPage.tsx
/opt/data/agent-os/apps/dashboard/frontend/src/pages/ObservabilityPage.tsx
```

---

## hermes-webui Parity Checklist

| Feature | hermes-webui | Phase | HWC Status |
|---------|-------------|-------|-----------|
| Session CRUD | ✅ | 1 | Not started |
| Session FTS | ✅ | 1 | Not started |
| Session projects/tags | ✅ | 1 | Not started |
| Streaming SSE | ✅ | 1 | Not started |
| Tool call cards | ✅ | 1 | Not started |
| Approval cards | ✅ | 1 | Not started |
| Profiles | ✅ | 1 | Not started |
| Skills | ✅ | 1 | Not started |
| Cron | ✅ | 1 | Not started |
| Memory | ✅ | 1 | Not started |
| Slash commands | ✅ | 1 | Not started |
| Themes (7) | ✅ | 1 | Not started |
| Auth | ✅ | 1 | Not started |
| Tiling WM | ❌ | 2 | Working |
| Keyboard shortcuts | ❌ | 2 | Working |
| Docker management | ❌ | 3 | Partial |
| Observability | ❌ | 3 | Partial |
| Command palette | ❌ | 4 | Not started |
| MCP | ❌ | 4 | Not started |
| Voice | ❌ | 4 | Partial |
| Electron shell | ❌ | 5 | Not started |

---

## Critical Questions Before Phase 1

1. **Database:** SQLite (modernc.org/sqlite, no CGO) or JSON files? SQLite faster for FTS but adds dependency.
2. **Session location:** `~/.hermes/agent-os/` or configurable via env?
3. **hermes-webui compatibility:** Should Agent-OS READ hermes-webui session files (for migration)?
4. **Multi-user:** Single-user design or multi-user from start?
5. **MCP:** Official MCP SDK or hand-rolled?

These must be answered before Phase 1 begins. See `docs/ROADMAP.md` for full discussion.
