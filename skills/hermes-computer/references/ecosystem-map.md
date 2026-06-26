# Ecosystem Map — ChonSong Repos

> Investigated 2026-05-14 as part of repo consolidation analysis.

## The Three Named Repos

| Repo | GitHub | Last Commit | Lines | Status |
|------|--------|-------------|-------|--------|
| `hermes-web-computer` | ChonSong | 2026-05-13 | 8.5K (4.8K Go + 3.5K FE) | Active dev target |
| `agent-os` | ChonSong | 2026-05-11 | React/Express/Postgres | Legacy, running prod on :3001 |
| `hermes-computer-planning` | ChonSong | 2026-05-11 | Docs only, no code | Archive candidate |

## hermes-web-computer
- **Purpose:** The tiling AI desktop — Go backend + Svelte 5 SPA
- **Stack:** Go 1.25 + Svelte 5 + Vite + Tailwind + xterm.js
- **Active development** — port 5174 (FE) + 3112 (BE)
- **Canonical SPEC:** `/opt/data/hermes-web-computer/SPEC.md`

## agent-os (Legacy — NOT a candidate for merger)
- **Purpose:** React dashboard — 22 pages, 11 themes, Express backend, Postgres DB
- **Stack:** React 19 + Express + Socket.IO + PostgreSQL 16 (8 migrations)
- **Still running** via Cloudflare tunnel on port 3001
- **State:** 525 sessions, 51K messages in Postgres
- **Migration source** — components migrated to HWC (DashAnalytics, DashOverview, etc.)
- **Key files:**
  - `apps/dashboard/backend/src/index.ts` — Express API (75+ routes)
  - `apps/dashboard/frontend/src/pages/` — 21 React pages
  - `infra/postgres/migrations/` — 8 SQL migrations
  - `STATE_OF_AGENT_OS.md` — detailed known issues

## hermes-computer-planning (Archive candidate)
- **Purpose:** Competitive analysis + planning docs
- **No code, no CI, no tests** — not a real repo by ChonSong standards
- **All useful content already duplicated** in `hermes-web-computer/`
- **Archive:** Move `completion-plan.md`, `APPLICATION-PLAN.md`, `ONE-WEBSITE.md`, `ILLOGICAL-IMPULSE-DESIGN.md`, `AUTONOMOUS-EXECUTION-PLAN.md` to `hermes-web-computer/docs/`, then archive

## External Repos (Not ChonSong)

| Repo | Owner | What it is |
|------|-------|-----------|
| `hermes-workspace` | outsourc-e | React Electron desktop UI for Hermes Agent — 794MB, very active (last push 2026-05-07), completely separate project |
| `hermes-docs-reference.md` | ChonSong | Local file, not a repo |

## hermes-sync (Separate, adjacent)
- **Purpose:** Portable config + skills bootstrap for any Ubuntu machine
- **Location:** `/opt/data/hermes-sync` (61MB)
- **Not part of the three repos**

## Key Findings

1. **Do NOT merge agent-os into hermes-web-computer** — different stacks (Express vs raw Go, React vs Svelte, Postgres vs SQLite), and agent-os is running in production
2. **Archive hermes-computer-planning** after moving its docs to HWC
3. **hermes-workspace is external** — owned by Eric (outsourc-e), not ChonSong, completely separate
4. **SPEC.md moved** — was accidentally written to agent-os/SPEC.md; now correctly at `hermes-web-computer/SPEC.md`