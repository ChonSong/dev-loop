---
name: web-app-factory
description: Repeatable workflow for building web applications — from idea to deployed app. Covers 5 app types (clones, landing pages, dashboards, full-stack apps, static sites) with the right tool at each phase.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [web-app, workflow, factory, repeatable, prototype, production, deploy]
    track: workflow
---

# Web App Factory — Repeatable Workflow

A decision-driven workflow that picks the right tool for the right phase, every time. No reinventing, no ad-hoc choices, no "which approach should I use?" — just follow the decision tree.

## Decision Tree: Which Path?

```
What are you building?
│
├── CLONE of an existing live site → Path A (Site Clone)
├── Design from SCREENSHOT/MOCKUP → Path B (Screenshot-to-Code)
├── "Make it look like [BRAND]" → Path C (Design System Template)
├── Full-stack APP with backend → Path D (Full-Stack App)
├── LANDING PAGE / marketing → Path E (Landing Page)
└── DASHBOARD / internal tool → Path F (Dashboard)
```

---

## Path A: Site Clone (from URL)

**Tools:** Open Lovable → me for production hardening
**Time:** Minutes to visual prototype, hours to production app

### Phase 1: Visual Prototype (2-5 min)

```bash
cd /workspace/open-lovable
npm run dev  # → http://localhost:3000
```

1. Open the app, paste the URL
2. Let it scrape + generate React/Vite/Tailwind code
3. Iterate with chat: "make the hero section more compact", "fix mobile nav"
4. Export the generated project files

### Phase 2: Production Hardening (me)

1. Read the generated files from `/tmp/open-lovable-sandboxes/`
2. Scaffold a proper repo with `repo-init`
3. Port the visual components into the real project structure
4. Add: auth, API routes, database schema, state management
5. Wire up CI/CD, deploy

**When to skip Open Lovable:** Site is JS-heavy SPA, behind auth, or mostly dynamic content. Fall back to Path C with visual reference.

---

## Path B: Screenshot-to-Code (from image/mockup)

**Tools:** `screenshot-to-code` (Docker) → me for production hardening
**Time:** Minutes to visual prototype, hours to production app

### Phase 1: Setup (one-time)

```bash
cd /workspace
git clone https://github.com/abi/screenshot-to-code.git
cd screenshot-to-code
echo "OPENAI_API_KEY=..." > .env
echo "ANTHROPIC_API_KEY=..." >> .env
docker-compose up -d --build
# → http://localhost:5173
```

### Phase 2: Generate Code

1. Drop in screenshot / Figma export / screen recording
2. Pick output stack (React+Tailwind, Vue+Tailwind, HTML+Tailwind)
3. Iterate with chat

### Phase 3: Production Hardening (me)

Same as Path A Phase 2.

---

## Path C: Design System Template ("make it look like Stripe/Linear/etc")

**Tools:** `popular-web-designs` skill (54 templates) → `sketch` for variants → me for build
**Time:** 10-30 min to production-quality frontend

### Phase 1: Load Design Tokens

```
1. skill_view("popular-web-designs", file_path="templates/stripe.md")
2. Extract: color palette, typography, component styles, shadows, spacing
3. If exploring: load 2-3 related templates (Stripe + Linear + Vercel)
   → use `sketch` skill to generate variants for comparison
```

### Phase 2: Build

**For static/landing pages:**
1. Create single-file HTML with design tokens as CSS custom properties
2. Use `single-file-html-apps` skill to deploy behind CF tunnel
3. Time: ~10 min

**For React/Next.js apps:**
1. `repo-init` → scaffold the project
2. Create `themes/<brand>-tokens.ts` with extracted design values
3. Build components using the token file
4. Deploy per project conventions

---

## Path D: Full-Stack App (backend + auth + database)

**Tools:** `repo-init` → Open Lovable or `popular-web-designs` for UI → me for logic
**Time:** 1-4 hours for V1

### Phase 1: Scaffold (5 min)

1. `repo-init` → monorepo with CI/CD, Docker, database
2. Stack decision (pick one per project, don't default):
   - **Next.js full-stack**: App Router + Server Actions + Drizzle + PostgreSQL
   - **React + FastAPI**: Vite frontend + Python API + PostgreSQL
   - **Go + React**: Go API server + Vite dashboard

### Phase 2: Visual Layer (10-30 min)

Two approaches — pick based on what you have:

| If you have... | Use |
|---|---|
| A reference URL | Path A (Open Lovable) → extract components |
| A brand name | Path C (popular-web-designs) → apply tokens |
| A screenshot | Path B (screenshot-to-code) → generate |
| A verbal description | Me directly → build from spec |
| **A static HTML file** | **Path G (HTML-to-Page) — see below** |

### Path G: HTML-to-Page (from a static HTML file)

**When:** User provides a single HTML file that IS the complete visual design.
**Technique:** Read the HTML, identify sections, rebuild as a Next.js client component.

#### Step 1: Parse the HTML structure
- Identify top-level sections: nav, header, main grid, panels, cells
- Extract the exact color palette (`:root` CSS vars or hardcoded values)
- Note interactive behaviors: hover effects, click handlers, active states
- Count grid dimensions and gap values

#### Step 2: Map to existing infrastructure
- Check if the project already has hooks for data fetching (`useStrategyLookup`, etc.)
- Check for existing UI components that match (heatmaps, charts, etc.)
- Don't rebuild what exists — wrap and restyle existing components

#### Step 3: Build as a single client component
- Use **inline styles** for pixel-perfect color/spacing matching to the HTML
- Use **CSS classes in globals.css** only for `:hover` effects and animations (can't do `:hover` inline)
- Extract repeated sub-components as named functions in the same file
  (`Panel`, `PanelHeader`, `PositionButton`, `HandMatrix`, `ActionCard`, etc.)
- Use `<style jsx>` (styled-jsx) sparingly for media queries that override inline styles

#### Step 4: Wire demo data first, API later
- Start with hardcode/data-generated strategy data to verify the visual
- Swap in the real hook (`useStrategyLookup`, etc.) once rendering is confirmed

#### Pitfalls
- **Don't use Styled JSX for everything** — it bloats the HTML with hashed class names. Prefer inline styles for one-off values.
- **Don't forget `overflow: "auto"` on the grid container** — matrices overflow on small screens.
- **`jsx-style` class collisions**: Styled JSX generates unique class names per component. If you use the same `<style jsx>` block in multiple components, they won't collide but will duplicate. Extract shared styles to `globals.css`.
- **Check PATH for `npx`/`next`**: In Nix/container envs, `npx` may not be on PATH. Verify with `which npx` first. If missing, prepend the user's local bin: `export PATH="/home/hermeswebui/.hermes/home/.local/bin:$PATH"` in the `terminal(background=true)` call.

### Phase 3: Logic Layer (me)

1. Database schema (from the app's domain model)
2. API routes / Server Actions
3. Auth (NextAuth, Clerk, or custom)
4. State management
5. Integration tests
6. Deploy

---

## Path E: Landing Page

**Tools:** `popular-web-designs` + `single-file-html-apps` OR `sketch` → deploy
**Time:** 15-60 min

### Decision: Single-file or framework?

| Criteria | Single-file HTML | Next.js/React |
|----------|-----------------|---------------|
| Needs no JS interactivity | ✅ | ❌ overkill |
| Single page, no routing | ✅ | ❌ overkill |
| Needs form → API → email | ✅ (fetch) | ✅ |
| Multiple pages/routes | ❌ | ✅ |
| CMS/blog | ❌ | ✅ |
| A/B testing | ❌ | ✅ |

### Single-file path (fastest):

1. Load design template: `skill_view("popular-web-designs", file_path="templates/stripe.md")`
2. Build HTML with embedded CSS + minimal JS
3. Deploy: `single-file-html-apps` skill → CF tunnel
4. Time: ~15 min

### Framework path:

1. Path D (Full-Stack App) with stripped-down config
2. Deploy: CF Pages or Vercel

---

## Path F: Dashboard / Internal Tool

**Tools:** `popular-web-designs` (dashboard designs) → me for data wiring
**Time:** 2-6 hours for V1

### Phase 1: Choose dashboard design

Best dashboard templates in `popular-web-designs`:
- **Linear** — ultra-minimal dark-mode, SaaS dashboards
- **Sentry** — data-dense, monitoring/alerting
- **PostHog** — playful, product analytics
- **Vercel** — clean monochrome, deployment dashboards
- **Kraken** — crypto/finance data-dense

### Phase 2: Scaffold (repo-init)

Dashboards almost always need a backend. Use Path D Phase 1.

### Phase 3: Wire up data

This is the hard part that templates can't do:
1. Define data sources (API endpoints, database queries, webhooks)
2. Build data-fetching layer (React Query, SWR, or Server Actions)
3. Connect components to real data
4. Add: auth, role-based access, real-time updates

---

## Deploy Decision Matrix

| App type | Best deploy target | Why |
|----------|-------------------|-----|
| Static HTML / landing page | **CF Pages** | Free, fast, you have the API key |
| Next.js SSR app | **Vercel** or **CF Pages** | Vercel is zero-config for Next.js; CF Pages if you prefer control |
| FastAPI backend | **Docker on host** | Full control, SSH accessible |
| Full-stack monorepo | **Docker Compose** | Frontend + backend + DB in one stack |
| Internal dashboard | **Docker + CF Tunnel** | Not public, tunnel gives access |

---

## Quick Reference: My Toolkit Inventory

| Tool | What it does | Best for |
|------|-------------|----------|
| `open-lovable-site-cloner` | URL → React/Vite/Tailwind app | Cloning live sites |
| `popular-web-designs` | 54 brand design systems as tokens | Building to a brand aesthetic |
| `sketch` | 2-3 throwaway HTML variants | Exploring design directions |
| `repo-init` | Monorepo scaffold + CI/CD + Docker | Full-stack app foundation |
| `single-file-html-apps` | Self-contained HTML → CF tunnel deploy | Landing pages, static sites |
| `cloudflare-tunnel` | Expose any local service publicly | Quick sharing, internal tools |
| Me | Code, refactor, debug, deploy, wire logic | Everything after prototype phase |

---

## Pitfalls

- **Don't start with Open Lovable for full-stack apps.** Start with repo-init, THEN bring in Open Lovable output for the visual layer. Otherwise you're fighting the Vite/Tailwind-only constraints while trying to add a database.
- **Don't skip the design tokens step.** Loading a popular-web-designs template and actually applying its values (vs guessing colors that "look right") is the difference between "obviously an AI clone" and "could be the real site."
- **Don't deploy from /tmp.** Open Lovable's sandbox writes to `/tmp/open-lovable-sandboxes/`. Always copy generated files into a properly initialized repo before committing.
- **Screenshot-to-code needs Docker.** If Docker isn't running on the host, fall back to Path C (design templates).
- **Don't pick a stack before understanding the domain.** A real-time collaborative dashboard needs a different stack than a blog. Ask first, scaffold second.
