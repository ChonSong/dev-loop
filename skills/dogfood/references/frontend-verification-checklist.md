# Frontend Verification Checklist — hermes-web-computer Pattern

> Discovered May 2026 during rigorous frontend verification session.

## The Problem

The `dogfood` skill's `browser_vision` calls hit vision API quota limits (429 errors) during intensive testing. When testing 14+ features with screenshots per feature, the quota exhausts quickly.

## The Solution: Multi-Layer Verification

When vision is unavailable or quota-limited, use this layered approach:

### Layer 1: DOM Inspection via browser_console

```javascript
// Check for specific CSS classes/design tokens
document.querySelector('[class*="glass"], [class*="backdrop"], [class*="blur"]')

// Count elements
document.querySelectorAll('button').length

// Check performance metrics
performance.getEntriesByType('resource').filter(r => r.name.includes('localhost'))

// Check for floating elements
document.querySelectorAll('[class*="floating"], [class*="FloatingTile"]')

// Check workspace store state
window.__workspaceStore?.activeWorkspace
```

### Layer 2: browser_snapshot

- Gets accessibility tree without vision API cost
- Shows all interactive elements with refs
- Can detect missing/extra elements

### Layer 3: browser_vision (use sparingly)

- Reserve for critical visual checks
- Use `annotate=true` to map refs to visual positions
- Expect 429 errors after ~5-10 calls in a session

### Layer 4: Direct CSS/JS verification

```javascript
// Check if specific CSS is applied
getComputedStyle(element).backdropFilter

// Check element visibility
element.offsetParent !== null

// Check WebSocket connection status
document.readyState
```

## The Feature Checklist Pattern

For comprehensive frontend verification, create a systematic checklist:

1. **Server Health** — HTTP status, process running
2. **Initial Load** — Page loads, assets load correctly
3. **Workspace System** — All workspaces switch, indicators highlight
4. **Design Tokens** — Glassmorphism, colors, fonts verified in DOM
5. **Terminal Tile** — Renders correctly, shows content
6. **Floating Windows** — Appear, chrome present, controls work
7. **Agent Chat** — Input works, send works, messages appear
8. **Browser/Dashboard Tiles** — Open, render content (not black screens)
9. **File Tree** — Navigation, breadcrumbs, file operations
10. **Command Palette** — Opens, fuzzy search works
11. **Panel Toggling** — Left/right panels collapse/expand
12. **Keyboard Shortcuts** — Shift+1-9, Shift+Alt+1-9, Shift+Space
13. **Drag-and-Drop** — FileTree → Editor, FileTree → Agent
14. **E2E Workflows** — Cross-panel interaction works

## The Report Pattern

Generate both markdown and HTML reports:

**Markdown**: Full details, steps to reproduce, issue classifications
**HTML**: Visual dashboard with status badges, metrics tables, screenshot gallery

Serve locally via `python3 -m http.server 8080` from the output directory.

## Critical Findings from First Run

| Issue | Root Cause | Fix |
|-------|------------|-----|
| Browser/Dashboard tiles show black screen | Component not mounting | Investigate tile rendering logic |
| Agent chat messages don't send | WebSocket connection issue | Check ws://localhost:3005/ws |
| Floating window controls don't work | Handlers not wired | Wire up minimize/close |
| Command palette missing | Not implemented | Implement UI |
| Vision API 429 errors | Quota exhaustion | Use DOM inspection fallback |
