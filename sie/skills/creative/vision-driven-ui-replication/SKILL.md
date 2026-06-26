---
name: vision-driven-ui-replication
description: Process for replicating real UIs from reference screenshots using vision analysis, structural blueprint extraction, and iterative QA comparison — until 90%+ visual similarity is achieved.
tags: [design, replication, vision, qa, iterative, frontend, ui-cloning]
related_skills: [gto-wizard-clone, popular-web-designs, claude-design, open-lovable-site-cloner]
---

# Vision-Driven UI Replication

A systematic process for cloning a real UI from screenshots. Works with any model — the secret is the **QA feedback loop**, not the model choice.

## Why This Works

The user's insight: *"if there is a robust process where a QA agent using vision analyses and development continues until it's 90% similar or more, any model will do."*

The core failure mode this prevents:
- **❌ Paint-by-classes**: Changing Tailwind colors to match without fixing the page LAYOUT
- **❌ Single-pass delivery**: Building from a prompt once and calling it done
- **❌ Token-only approach**: Applying a color palette without understanding component hierarchy

## Process

### Phase 1: Reference Discovery

```bash
mkdir -p /workspace/<project>-references
```

Find reference screenshots via:
1. **Product help sites** (e.g., help.gtowizard.com) — usually have annotated screenshots
2. **DuckDuckGo image search** — `curl -s "https://lite.duckduckgo.com/lite/?q=<product>+screenshot+<feature>"`
3. **GitHub repos** — search for images in related open-source projects
4. **Pricing / feature pages** — img tags on product website

Delegate discovery to a subagent with `web` + `terminal` toolsets.

Target: 10+ screenshots covering all major pages and states. Store all in `/workspace/<project>-references/`.

### Phase 2: Vision Analysis

For each key screenshot, use `vision_analyze` with TWO passes:

**Pass A — Structural Blueprint:**
```
Analyze this as a STRUCTURAL BLUEPRINT. List every visible element:
1. What it is (button, tab, matrix cell, label, input)
2. Its exact position (what's above/below/left/right)
3. Its size (approximate px)
4. Its color and text content
5. Its interactive behavior

Draw an ASCII tree of the FULL PAGE LAYOUT — every container, parent-child relationships.
```

**Pass B — Design Tokens:**
```
Extract pixel-level design details:
1. Exact background hex colors
2. Font sizes and families
3. Component dimensions (cell sizes, bar heights, button padding)
4. Color palette for every UI state (active, inactive, hover)
5. Spacing grid (gaps, margins, paddings)
```

**Critical questions to ask:**
- "Is this screenshot showing the FULL PAGE or just a cropped panel?"
- "How many [matrices/panels/tabs] are visible?"
- "What elements are positioned to the LEFT / RIGHT / BELOW the main area?"
- "How does the sidebar interact with the main content area?"

### Phase 3: Structural Implementation

Build the page LAYOUT first, colors second.

1. **Create component hierarchy** — match the ASCII tree from Phase 2
2. **Use semantic containers** — nav bar, position flow bar, sub-tabs, matrix area, stats bar, graph, sidebar
3. **Populate with placeholder/stub content** — get the structure right first
4. **Apply design tokens** — only after structure is correct
5. **Wire real data** — connect to API endpoints last

**Signs you're still in paint-by-classes mode:**
- The page has the right colors but wrong number of columns, panels, or sections
- Components are in different positions than the reference
- A major UI element (tab bar, sidebar, position flow) is missing entirely

### Phase 4: Structural Comparison Table

Build a table mapping reference layout against current code:

| Reference Element | Code Location | Status | Gap Type |
|-----------------|---------------|--------|----------|
| Position flow bar | `PositionFlowBar` component | ✅ exists | — |
| Dual matrices side-by-side | `HandMatrix` ×2 | ⚠️ heroRange empty | DATA |
| Stats with 4 columns | Grid in page.tsx | ✅ exists | — |
| Equity line graph | `EquityChart` | ❌ fake Math.sin data | MOCK |
| Bottom tabs | JSX in page.tsx | ⚠️ "coming soon" | PLACEHOLDER |

**Do NOT proceed until all structural gaps are closed.** Color/font polish on a structurally wrong page wastes effort.

### Phase 5: Bug Taxonomy

When cross-referencing code against vision-extracted layout, search systematically:

| Bug Category | What to Check | Example from Session |
|-------------|---------------|----------------------|
| **Grid breakage** | Custom grid values exist in Tailwind config? | `grid-cols-14` missing → all 169 matrix cells stacked vertically |
| **Data flow** | Does state A populate when state B changes? | `heroRange` never synced from `villain` input — left matrix always empty |
| **Parsing** | String-to-component mapping correct? | `board.split("")` splits "Kd7h2c" into 6 chars, not 3 cards |
| **Formula** | Derived values use real computation, not placeholders? | EQR = `ev_per_hand/100 + 0.5` — completely wrong formula |
| **Dead code** | Imported/unused components or variables? | `MatrixCell` component never rendered; unused `gto` import |
| **Placeholders** | "Coming soon" / TODO visible in rendered output? | 3 bottom tabs showing "coming soon" instead of real content |
| **Mock data** | Real API call or fake random data? | Equity chart using `Math.sin`/`Math.cos` instead of actual result data |
| **URL proxy** | Frontend rewrites exist for all API paths? | Missing Next.js rewrites for `/icm/*`, `/plo4/*` → 404s |

### Phase 6: Fix → Verify → Loop

```
┌─────────┐    ┌───────────┐    ┌──────────────┐    ┌──────────┐
│ BUILD   │───▶│ QA CHECK  │───▶│ VISION       │───▶│ FIX      │
│ (code)  │    │ (struct)  │    │ COMPARE      │    │ (diff)   │
└─────────┘    └───────────┘    │ (vs ref)     │    └──────────┘
                                └──────────────┘         │
                                       │                  │
                                       ▼                  │
                                 ┌──────────┐             │
                                 │ < 90%?   │──── yes ────┘
                                 │ >= 90%?  │──── DONE
                                 └──────────┘
```

#### Automated Visual Regression (Puppeteer Pipeline)

If a Puppeteer-based QA tool exists (e.g., `/workspace/ui-qa-tool/ui-qa.js`), use it for pixel-accurate visual comparison instead of manual `vision_analyze`:

```bash
# First run — capture reference screenshots for all pages
ui-qa pipeline http://localhost:8555

# After changes — detect what broke visually (pixel-diff against references)
ui-qa pipeline http://localhost:8555

# Individual commands
ui-qa snapshot <url> <name>                       # Screenshot + metadata
ui-qa diff <ref.png> <current.png>                # Pixel-accurate diff with red overlay
ui-qa audit <url>                                 # Console errors, HTTP errors, a11y, perf
ui-qa check <url> --selectors=h1,.nav,#matrix     # Verify specific elements exist & visible
```

**The pipeline config** is at `ui-qa-pages.json` — a JSON object mapping page names to URL paths:
```json
{
  "equity": "gto/equity",
  "solver": "gto/solver",
  ...
}
```

**What the pipeline reports:**
- ✅ Pass: <1% pixel diff — no significant visual change
- 🔶 Minor: 1-5% pixel diff — slight layout shifts (acceptable)
- ❌ Failed: >5% pixel diff — visual regression detected

**Console errors are also captured** — the pipeline checks for JS errors, HTTP 500s, and a11y violations on every page.

#### Iteration Loop

Each iteration:
1. **Fix one bug at a time** with targeted `patch()` calls (not full rewrites)
2. **Verify TypeScript**: `npx tsc --noEmit --pretty`
3. **Rebuild**: `next build`
4. **Proactively kill zombie processes** before restarting (see Port Conflict pitfall)
5. **Restart server** with correct PATH (see Background Process pitfall)
6. **Verify HTTP 200**: `curl -s -o /dev/null -w "%{http_code}" http://localhost:PORT/page`
7. **Run QA check**: structural checklist (`python3 /workspace/gto-vision-qa.py all`)
8. **Run visual pipeline**: `ui-qa pipeline http://localhost:8555` — compare against reference screenshots
9. **Check console errors** from pipeline report — identify JS errors and API 500s
10. **Loop** until all gaps closed and pipeline reports 0 failures

### Phase 7: QA Automation

Build a structural QA script that checks source code for required components:

```python
checks = {
    "13x13 hand matrix": ["grid-cols-14", "HandMatrix", "handName"],
    "position flow bar": ["PositionFlowBar", "UTG", "HJ", "CO", "BTN", "SB", "BB"],
    "dual matrices": ["heroRange", "parseRange(villain)"],
    "stats panel": ["Combos", "EV", "Equity", "EQR"],
}

for section, patterns in checks.items():
    missing = [p for p in patterns if p not in content]
    if missing:
        file_issue("STRUCTURE", f"Missing in {section}", f"Patterns: {missing}")
```

Run via: `python3 /workspace/gto-vision-qa.py all`

### Phase 8: Tokenization

Extract design tokens into a shared file (`styles/<project>-tokens.ts`):

```typescript
export const tokens = {
  colors: { bg: "#1a1a1a", card: "#2a2a2a", accent: "#00C9A7", /* exact hex */ },
  font: { family: "Inter", sizes: { h1: 16, body: 13, label: 11 } },
  spacing: { sidebar: 280, matrixCell: 38, matrixGap: 2 },
} as const;

export function actionColor(action: string): string { /* map action→hex */ }
export function equityColor(eq: number): string { /* map 0-1→color */ }
```

## Pitfalls

### ❌ Structure Before Paint Is Not Optional
The #1 mistake: updating Tailwind color classes (`bg-gray-800` → `bg-[#2a2a2a]`) while keeping a completely different page layout. The user will say "still nothing like the original" because the layout is wrong underneath.

**Fix:** Build the complete component hierarchy first. Verify the number and position of every panel/section before touching a single color value. Use the comparison table (Phase 4) to track progress.

### ❌ Subagents Cannot Do Design Work
Subagents (delegate_task with cheaper models) produce pages that:
- Use mock/fake data instead of real API calls
- Don't load reference skills (popular-web-designs, claude-design)
- Skip structural analysis and jump to implementation
- Create large page blobs with wrong component hierarchy

**Fix:** Do structural extraction and component mapping yourself. Use subagents only for mechanical work (API wiring, data formatting) and **verify every rendered output** — a subagent saying "file written successfully" is a self-report. `git diff` and curl the actual page.

### ❌ Vision Analysis of Cropped Screenshots
A screenshot might show just one panel (e.g., a board texture filter popup) rather than the full page. Always:
- Cross-reference multiple screenshots of the same page
- Ask vision_analyze: "Is this the full page view or a cropped panel?"
- Look for product help/pricing pages which show full-page layouts with navigation

### ❌ Tailwind Semantic Colors vs Hex Values
Tailwind's `gray-400`, `emerald-600`, `border-gray-700` don't match real UI colors. Tools like GTO Wizard use specific dark palettes that require explicit `#888`, `#00C9A7`, `#3a3a3a` values.

**Search for stale semantic classes before deploying:**
```bash
grep -n "bg-gray-\|text-gray-\|border-gray-\|bg-emerald-\|ring-" /workspace/*/app/gto/*/page.tsx
```
If any remain, convert to explicit hex values.

### ❌ Custom Grid Utilities
Poker UIs need `grid-cols-13` and `grid-cols-14` — not in default Tailwind. Always add to `tailwind.config.ts`:

```typescript
extend: {
  gridTemplateColumns: { '13': 'repeat(13, minmax(0, 1fr))', '14': 'repeat(14, minmax(0, 1fr))' },
  gridTemplateRows: { '13': 'repeat(13, minmax(0, 1fr))', '14': 'repeat(14, minmax(0, 1fr))' },
}
```

### ❌ Zombie Process Port Conflicts (no fuser/ss)
Containers lack `fuser -k` and `ss -tlnp`. Universal fallback using `/proc/net/tcp6`:

```bash
# 1. Find port hex: 8555 = 0x216B
cat /proc/net/tcp6 | grep -i "216B"
# Output: ...:216B ...:0000 0A ...  (note inode number in field 10)

# 2. Find PID by inode (field 10 from above, e.g. 8061004)
for f in /proc/*/fd/*; do
  link=$(readlink $f 2>/dev/null)
  if echo "$link" | grep -q "socket:\[8061004\]"; then
    pid=$(echo $f | cut -d/ -f3)
    echo "PID=$pid holds port 8555 ($(cat /proc/$pid/cmdline | tr '\0' ' '))"
    kill -9 $pid
  fi
done
```

**ANTI-PATTERN — kills the shell itself:**
```bash
# DON'T DO THIS — the for loop /proc/* iteration includes the shell PID
for pid in $(ls /proc/*/cmdline); do
  ...
done
```

### ❌ Background Process PATH
Background `terminal(background=true)` processes do NOT inherit PATH. Always:

```bash
# CORRECT:
export PATH="/home/hermeswebui/.hermes/home/.local/bin:$PATH"
./node_modules/.bin/next start -p 8555

# WRONG — npx won't be found:
npx next start -p 8555
```

### ❌ Server Restart Timing
After starting a background server process, don't `sleep N` — poll rapidly:

```bash
# CORRECT:
for i in 1 2 3 4 5; do
  curl -s -o /dev/null -w "%{http_code}" http://localhost:8555/page && break
  sleep 2
done
```

## HTML Reference to Next.js Migration

A complementary workflow to screenshot-based replication: when the user provides a **source HTML file** as the design reference, the process shifts from "vision analysis" to "code extraction and conversion."

### When This Applies

- User provides a `.html` file as the design spec
- User says "here's the code I want you to adapt"
- The HTML contains inline CSS, vanilla JS, and markup that needs converting to React/Next.js

### Process

#### Step 1: Extract CSS Design System

The reference HTML's `:root` block defines the entire design language. Extract it verbatim into `globals.css`. **Preserve exact hex values** — do NOT map to Tailwind semantic colors. `--bg: #0E0E0E` must stay `#0E0E0E`, not `bg-gray-950`.

Add `@media` responsive rules from the reference verbatim too — these carry layout breakpoints that are easy to miss.

#### Step 2: Convert Nav to React Component

The reference HTML `<nav class="top-nav">` becomes a `Header.tsx` component. Map HTML elements to React:

| HTML | React |
|------|-------|
| `.logo` div | Link + green square + "W" |
| `.nav-tab` links | Array of `{href, label, badge?, highlight?}` → `<Link>` |
| `.nav-tab.green` | Conditional green bg when active (`tab.highlight && pathname === tab.href`) |
| `.btn-upgrade` | Button with crown emoji |
| `.icon-btn` | Buttons with emoji icons (⬆, ⛶, ?, ⚙) |
| `.avatar` | Gradient circle with letter |

Active state: `usePathname()` from `next/navigation`. Map multiple paths to the same tab when needed (e.g., `/study`, `/strategy`, `/strategies` all map to "Study").

#### Step 3: Convert Page Layout to Next.js

The two-column grid (`<main class="app">`) becomes the page component. Each `<section class="panel">` becomes a div with the reference's exact `background`, `border`, and `borderRadius` values.

Page uses `"use client"` directive for interactivity. Mark pages as `export default function PageName()`.

#### Step 4: Extract State Machine from Vanilla JS

Reference HTML often uses imperative DOM manipulation that must be converted to React state. Key patterns:

**Pattern A: "Fill next empty slot" UX (poker calculator)**
```
Vanilla JS: `getNextTarget()` iterates slots in order, returns first null
→ React: `useMemo` computes `nextTarget` from current state, `selectCard(card)` fills it
→ State: `useState` for you/board/player card arrays
→ Disable used cards: `useMemo` computes `allUsed` → `isUsed(card)` check
→ Remove card: click handler on filled card sets slot to null
```

**Pattern B: Matrix rendering with color map**
```
Vanilla JS: `rows.flat().forEach(hand => { createElement('div'); style.background = bg[hand] || BLUE })`
→ React: `MATRIX_HANDS.flat().map(hand => <div style={{background: getCellColor(hand)}} />)`
→ Color map (red set, gradient conditions) reproduced exactly
```

**Pattern C: Auto-calculating simulation**
```
Vanilla JS: Calls `update()` at end of every mutation → triggers `runCalc()`
→ React: `useEffect` with dependency on allUsed triggers Monte Carlo
→ Debounce: `setTimeout(50)` with cleanup via `useRef(cancelled)`
```

#### Step 5: Preserve Vanilla JS Engines as Utilities

When the reference HTML includes a computational engine (hand evaluator, Monte Carlo, etc.), extract it as-is into the React component rather than calling a backend API. These engines are self-contained, fast enough (2000 iterations <50ms), and more responsive than network round-trips.

**Keep the exact engine code** — don't refactor or "clean up" working combinatorial logic. The reference JS has been tested. Changes introduce bugs.

**Example: poker hand evaluator**
```typescript
const COMBOS5 = (() => { /* ... */ })()  // verbatim copy
function evaluate5(hand: Card[]): number { /* verbatim copy */ }
function evaluate7(cards: Card[]): number { /* verbatim copy */ }
```

#### Step 6: Positioning Layout Elements

The reference HTML uses absolute positioning with percentage coordinates for table seats. Port these verbatim but wrap in React inline styles:

```tsx
{ id: 3, left: '1%', top: '50%', label: 'Player 3' },
{ id: 4, left: '9%', top: '18%', label: 'Player 4' },
```

**Pitfall:** Absolute children inside a parent with `transform: translate(-50%, -50%)` can conflict. Use a wrapper div for the centered element, not the same container as absolute children.

#### Step 7: Build and Deploy

```bash
export NEXT_PUBLIC_API_URL=http://localhost:8003
npx next build
# Kill stale server (process group kill)
find /proc -maxdepth 2 -name "cmdline" | while read cmd; do
  if grep -qa "next start" "$cmd" 2>/dev/null; then
    kill -9 -$(cat /proc/$(echo $cmd | cut -d/ -f3)/stat | awk '{print $5}')
  fi
done
npx next start -p 8564
```

### Pitfalls

- **Inter font** — Add Google Fonts link to `layout.tsx`.
- **Kill stale servers with process group** — `pkill -f "next"` misses. Use process group kill. WARNING: `find /proc` loops can kill the shell itself (exit -9). Keep commands short.
- **`NEXT_PUBLIC_*` at build time** — Set before `npx next build`, not at runtime.
- **CSS vars in inline styles** — React inline styles don't resolve `var(--bg)`. Use raw hex.
- **Responsive breakpoints** — Preserve reference HTML's `@media` rules in `globals.css`.
- **Monte Carlo on every render** — Use `setTimeout(50)` + `useRef(cancelled)` to prevent stacking.
- **Card selector disabled state** — Use `pointerEvents: 'none'` AND `opacity: 0.28`. `disabled` alone doesn't prevent hover.
- **"Add player" toggle** — Set `display: none` when active, not just conditional render.

## Support Files

### `scripts/structure-qa-template.py`
Template for building a structural QA checker script. Customize for each project.

### `references/bug-taxonomy.md`
Full bug taxonomy table with detection patterns for each bug category and real examples.

## Related Skills

- **gto-wizard-clone** — Largest deployment of this process (14 pages, 81 API endpoints, 50+ reference screenshots, structural QA pipeline at `/workspace/gto-vision-qa.py`)
- **software-development/systematic-debugging** — Debugging patterns that complement this UI-replication process
- **popular-web-designs** — Reference design systems for general UI inspiration when no specific target UI exists
- **claude-design** — Generative design process (use for NEW designs; this skill for RECREATING existing ones)
