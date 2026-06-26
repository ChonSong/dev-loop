# Autonomous Gap Detection — Project Setup Guide

The coach-agent's Phase 2.5 (Spec Gap Detection) autonomously finds missing features
across three layers. This guide explains how to configure each layer per project.

## Three Layers of Gap Detection

```
Layer 3: Generic Heuristics (no setup required)
  ├── Route inventory — finds all page files, flags stubs under 30 lines
  ├── API endpoint scan — discovers route definitions, curls a sample
  ├── Stub/placeholder grep — "TODO", "WIP", "coming soon", "TBD"
  ├── Component dead/dangling — counts imports from components/ dir
  └── Velocity tracking — tasks/day vs. spec gaps shrinking?
          ↑ Works on ANY project with AGENTS.md — zero config

Layer 2: FEATURES.yaml (per-project checklist — RECOMMENDED)
  ├── Machine-readable spec of every route, component, API
  ├── Items marked "missing" auto-generate backlog tasks
  └── Coach verifies each item against live codebase

Layer 1: Reference Screenshots (visual — OPTIONAL)
  ├── .png/.jpg in docs/ or designs/ directory
  ├── Coach auto-discovers them, loads via vision_analyze
  ├── Compares against browser_snapshot of the route
  └── Flags mismatches as spec gaps
```

## When to Set Up Each Layer

| Project type | Layer 3 (heuristics) | Layer 2 (FEATURES.yaml) | Layer 1 (screenshots) |
|---|---|---|---|
| New project, first week | Always on — finds stubs naturally | Skip — too early, features undefined | Skip — nothing built yet |
| Active project with UI | Always on — catches stubs | Set up — this is where the coach shines | Add for key pages that need visual matching |
| API/microservice (no UI) | Always on — catches missing endpoints | Optional — endpoint list is useful | N/A |
| Legacy project takeover | Always on — discovers page inventory | High value — maps current state vs. gaps | Skippable unless redesigning |

## Setting Up Layer 2: FEATURES.yaml

### Step 1: Create the file

Copy the template from `coach-agent/references/features-yaml-template.yaml` to the project root as `FEATURES.yaml`.

### Step 2: Inventory routes

Run in the project root:

```bash
# Next.js App Router
find apps/web/src/app -name "page.tsx" -o -name "page.jsx" | sort

# SvelteKit
find src/routes -name "+page.svelte" | sort

# Flask/FastAPI HTML templates
find templates -name "*.html" | sort

# Generic web app
find . -name "*.html" ! -path "*/node_modules/*" | sort
```

For each route, add an entry under `pages:`.

### Step 3: Inventory components

For each route, inventory the UI components it should have:

```bash
# What components exist?
find apps/web/src/components -name "*.tsx" | sort

# What does each page import?
grep "from '@/components" apps/web/src/app/study/page.tsx
```

List each expected component under the route's `components:` section.

### Step 4: Inventory API endpoints

```bash
# FastAPI
grep -rhE "@(router|app)\.(get|post|put|delete|patch)\(" apps --include="*.py" | grep -v __pycache__ | sed 's/.*("\([^"]*\)").*/\1/' | sort

# Express
grep -rhE "(router|app)\.(get|post|put|delete|patch)\(" apps --include="*.js" --include="*.ts" | sed 's/.*("\([^"]*\)").*/\1/' | sort
```

List under the relevant route's `apis:` or under the global `apis.general:`.

### Step 5: Set statuses

- `present` — feature exists, works, and has tests
- `missing` — feature is planned but not built yet (coach generates tasks)
- `stub` — page exists but has placeholder content (coach flags it)
- `broken` — page exists but returns 500/404 at runtime (coach generates fix task)

### Step 6: Verify the coach picks it up

The coach reads FEATURES.yaml during Phase 2.5 of its next review cycle. You can verify by checking `.checkpoint.json` for the `spec_gaps` array after the coach runs.

## Setting Up Layer 1: Reference Screenshots

### Convention

Place reference screenshots in the project's `docs/` directory. Name them descriptively:

```
docs/reference-study-interface.png     → route: /study
docs/reference-home-layout.png         → route: /
docs/designs/quiz-card.png             → route: /quiz
```

### What makes a good reference image

- Shows the COMPLETE interface (not a cropped fragment)
- Has all interactive elements visible (buttons, inputs, cards)
- Shows the expected state (not a loading/empty state)
- Uses the same theme/dark mode as the target

### Coach comparison flow

When the coach finds a reference image during Phase 2.5:

1. `vision_analyze(<image>)` — understand layout, elements, colors
2. `browser_navigate(<route>)` — load the live page
3. `browser_vision()` — screenshot the rendered output
4. Compare: are the same UI elements present? Button positions? Layout structure?
5. Flag any specific missing components as individual spec gaps

### Pitfalls

- **Login-walled references**: If the reference shows a service behind login (e.g., real GTO Wizard), the coach can still analyze the image for layout/structure even though it can't load the live equivalent. Flag as "layout target" rather than "pixel match."
- **Stale references**: If a reference image matches a past version of the product, the coach may flag false gaps. Update reference images when the target design changes.
- **Multiple references per route**: If multiple .png files map to the same route, the coach picks the most recently modified one.

## Verifying the Setup

After setting up Layers 2 and/or 1, run this to verify:

```bash
# Does FEATURES.yaml exist?
ls FEATURES.yaml

# Does it have the expected format?
grep "route:" FEATURES.yaml | head -5
grep "status: missing" FEATURES.yaml | wc -l  # → count of known gaps

# Do reference images exist?
find docs -name "*.png" -o -name "*.jpg" 2>/dev/null | head -10
```

The coach's next run will discover these and include them in the backlog health check.

## What Each Layer Discovers

| Gap type | Layer 3 alone | Layer 2 added | Layer 1 added |
|---|---|---|---|
| Missing page route | ✅ Detects if file doesn't exist | ✅ Confirms with spec | ✅ Visual comparison possible |
| Stub page (<30 lines) | ✅ Detects via size heuristic | ✅ Confirms with status: stub | ✅ Can see placeholder visually |
| Missing API endpoint | ✅ Detects if no matching route def | ✅ Confirms endpoint is in spec | — |
| Missing UI component | ❌ Can't know what components should exist | ✅ Each component listed explicitly | ✅ Can see if component is missing from screenshot |
| Layout mismatch | ❌ No reference | ❌ No reference | ✅ Reference image comparison |
| Color/spacing/theme issues | ❌ | ❌ | ✅ Can compare theme visually |
