# Adapting External Libraries Into a Monorepo

This reference covers the pattern for adapting an external library (C++, Python, etc.) into a monorepo with FastAPI backend and Next.js frontend.

## 3-Layer Pipeline

```
Layer 1: Core Module ──→ Tests ──→ API Router ──→ Frontend Page
          (wrapper +       (pytest       (FastAPI         (Next.js
           logic           before        + Pydantic        page)
           modules)        impl)         schemas)
```

**Layer 1 — Core Module (`packages/{domain}/src/{package}/`):**
- Create the main wrapper class using the external library's API
- Write a companion calculator (Monte Carlo if enumeration is too expensive)
- Write a parser if needed (string notation → concrete data structures)
- Each file is independent and testable

**Layer 2 — API Router (`apps/{api}/routers/`):**
- FastAPI router with POST endpoints wrapping the core module
- Pydantic request/response models
- WebSocket endpoint for streaming/long-running calculations
- Error handling: 422 for bad input, 500 for internal failures

**Layer 3 — Frontend Page (`apps/{web}/src/app/{route}/page.tsx`):**
- Client component (`"use client"`) calling the API
- Loading/error/empty states
- Responsive design matching existing theme

## Cron-Driven Autonomous Completion

For large projects, drive completion via cron jobs with attached skills. See `references/cron-job-pattern.md` for the full cron job prompt structure.

Each cron tick should attempt ONE sub-task with clear success criteria. If the sub-task is already done (files exist), skip to the next one. Use `delegate_task` for complex sub-tasks that might time out.
