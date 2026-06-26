# System Architecture Reference

The full system architecture is documented at `/home/sc/workspace/system-architecture.md` (1,064 lines).

This document describes how the autonomous development loop fits into the broader system:

## Three Pipelines

**Development (Maker)** — Player (every 2h) → Coach (every 4h) → Checkpoints → Git

**Monitoring (Keeper)** — Netdata (:19999) → energy-router /metrics → Discord alerts (#alerts)

**Quality (Checker)** — promptfoo CI → Backend tests (17) → Docker E2E (12 checks) → Coach reviews

## Key Architecture Points for the Dev Loop

- The Player's output flows through Coach before advancing checkpoints
- Coach reviews are stored in the master checkpoint (`review_quality` field)
- Netdata detects new services automatically when deployed via Docker
- The Player backlog comes from two sources: checkpoint priorities AND the seans-reporepo-query methodology

## Services the Dev Loop Maintains

| Service | Port | Type | Stack |
|---|---|---|---|
| Hermes System Console | :3030 | Dashboard | Go + Svelte 5 |
| GTO Wizard | :3000 | Web app | Next.js + FastAPI |
| Energy Router | :8009 | API | Python FastAPI |
| HWC | :3005 | Web app | Go + Svelte 5 |
| Polytopia | :3001 | Game server | Node.js |

## Port Summary (18 ports, all responding)

22→SSH, 3000→GTO, 3001→Polytopia, 3005→HWC, 5432→Postgres, 6379→Redis, 8001→GTO API, 8009→Energy-router, 8642→Hermes Gateway, 8787→Web UI, 9119→Dashboard, 19999→Netdata, 20241→Cloudflare tunnel

See `/home/sc/workspace/system-architecture.md` for complete failure modes, recovery procedures, and cron job reference.
