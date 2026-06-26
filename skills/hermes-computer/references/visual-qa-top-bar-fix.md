# Visual QA: Top Bar Color Fix (2026-05-24)

## What Was Wrong

The top bar (WorkspacePill) was `#65626c` instead of `#1c1c1d`. The inactive pill `bg-black/40` Tailwind class was producing a mid-gray (`#666666` blended), not the near-black reference color.

## The Fix

Changed from CSS class-based background to **inline style**:

```svelte
<!-- BEFORE (class-based, too bright) -->
<div class="... bg-black/40 ...">

<!-- AFTER (inline style, exact match) -->
<div style="background-color: #1c1c1d; opacity: 0.95;">
```

**Why inline style won:** When you need to hit a specific pixel color from a reference, Tailwind's opacity blending produces approximate midpoints. Direct `style="background-color: #1c1c1d"` locks the exact value. Inline styles override Tailwind classes in the cascade.

## Verified Pixel Values

| Location | Reference | Before | After |
|----------|-----------|--------|-------|
| top_bar center (720,30) | #1c1c1d | #65626c | #1c1c1d ✅ |
| top_bar left (600,30) | #1c1c1d | — | #1c1c1d ✅ |
| top_bar right (800,30) | #1c1c1d | — | #1c1c1d ✅ |
| overall vs reference | — | 81.8% | 81.9% |

The top_bar delta dropped from **73.3** to **1.4** — essentially perfect match.

## Server Detection

The HWC backend runs at **port 3005** (`./agent-os server --port 3005`), NOT 3113. Port 3113 was an SSH tunnel to an old server.

```bash
# Detect which port serves HWC:
curl -s http://localhost:3005/ | grep title  # → <title>Agent-OS v1.2</title> = HWC ✅
curl -s http://localhost:3113/ | grep title  # → empty = tunnel/old ❌
```

## Key Learning

When visual QA shows a specific color mismatch in a specific region:
1. Find the component (WorkspacePill.svelte)
2. Try **inline style** for exact colors — more reliable than Tailwind opacity classes
3. `bg-black/40` gives `#666666` at 40% opacity over transparent — not the same as `#1c1c1d`
4. After fix: rebuild (`npm run build`), restart server, re-screenshot with 60s virtual-time-budget

## Two-Server Trap

Two servers may be running:
- **Port 3005**: `agent-os server --port 3005` — HWC Go backend + Svelte SPA ✅
- **Port 3113**: Legacy SSH tunnel or old agent-os instance ❌

Always verify with `curl` title tag before screenshot comparison.