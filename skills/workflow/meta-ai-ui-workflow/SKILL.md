---
name: meta-ai-ui-workflow
description: Workflow for using meta.ai to generate UIs when the AI assistant lacks confidence in visual generation, then refactoring the output into production React components
---

# Meta.ai UI Generation Workflow

When the user lacks confidence in AI-generated UIs (or the AI itself recognizes its visual generation limits), use this workflow to delegate UI generation to meta.ai and handle the refactoring yourself.

## When to Trigger

- User explicitly states lack of confidence in AI-generated UIs → delegate to meta.ai immediately
- Building/refining UI components for the GTO Wizard Clone (Next.js 15 + Tailwind CSS 4)
- Any React frontend work where the user prefers visual quality from meta.ai
- Equity calculators, range selectors, training quiz UIs, hand viewers, variant selectors

## Autonomous Work Loop

The user wants indefinite operation with NO stalls. Never get blocked waiting for a decision.

### The Loop

```
1. Scan backlog for highest-priority task that does NOT need meta.ai
   -> Do it now. Commit. Move to next.
2. When you hit a visual UI component that needs meta.ai quality:
   -> Append exact prompt to .meta-ui-prompts.md.
   -> Skip it. Mark as "waiting: meta.ai" in the file.
   -> Move to next task immediately.
3. After each batch of work (3-5 commits or hitting a meta.ai blocker):
   -> Check if .meta-ui-prompts.md has accumulated prompts.
   -> If yes: present the batch to the user in a list.
   -> If no: continue to next task.
4. When backlog is exhausted, re-prioritize and start again from the top.
```

### Prompt Queue File

Store pending meta.ai prompts in `.meta-ui-prompts.md` at the repo root:

```markdown
# Pending UI Generations for meta.ai

## 1. [Component Name]
Priority: High/Medium/Low
Status: Not started
Route: /equity/2-7td

Prompt for meta.ai:

> *"... paste prompt here ..."*
```

When presenting to the user, emit a signal:

**🔴 UI GENERATIONS READY** — N prompts in .meta-ui-prompts.md

### Phase 1: Autonomous Work (no user needed)
- Backend API routes, solver logic, DB schemas, auth
- Dockerfiles, CI/CD, cron jobs, deployment, tunnels
- Test writing (unit + E2E), test infrastructure
- Architecture decisions, project structure, repo cleanup
- Code refactoring (any existing code → React components)
- Building page structure, API clients, component scaffolding — anything before the polished visual layer
- Rust/PyO3 bridge work (solver optimization — no UI)
- Repo consolidation, dead code removal

### Phase 2: UI Generation Request
When a polished UI component is needed and the task is the current highest priority:

**🔴 UI GENERATION NEEDED**

Then provide:
1. **Component name** and what it's for
2. **Exact prompt** for the user to paste into meta.ai (include visual style, layout requirements, dark theme)
3. **Instructions** to paste the raw HTML output back

User does NOT want browser-based automation for meta.ai (avoids captchas). Copy-paste is the preferred channel.

### Phase 3: Refactoring the Output
When the user returns the HTML:

1. Convert raw HTML → proper React/Next.js components
2. Extract inline styles → Tailwind classes or gtoTheme tokens
3. Replace mock data with real API calls (variantApi.equity(), etc.)
4. Split into logical sub-components
5. Add loading states, empty states, error handling
6. Wire to the existing API routes
7. Integrate into the app router page structure
8. Run build verification: `cd apps/web && npx next build 2>&1 | tail -10`
9. Commit: conventional commit message describing what was done + "from meta.ai"

### Phase 4: No Stalling - Infinite Loop
- Never end with "what should I do next?" — pick the next task and start
- Never end with "I'll wait for your response" — continue autonomous work
- Never skip a task because it's hard — at least assess it, create the page scaffolding, commit the structure

## Current Project Context

### GTO Wizard Clone
- **Repo**: `/home/sc/repos/gto-wizard-clone` on host
- **Frontend**: Next.js 15 App Router, React 19, Tailwind CSS 4
- **Backend**: Python FastAPI, gRPC solver, pokerkit variants
- **Deploy**: Port 3000, tunnel via codeovertcp, Cloudflare Access
- **Deploy after commit**: `docker stop gto-wizard-clone && docker rm gto-wizard-clone && docker run ...` on host

### Variants (backend complete):
NLH, PLO4, PLO5, Omaha8, Stud, Stud8, Razz, 2-7 TD, 2-7 SD, Badugi

### Frontend Routes:
| Route | Component | Status |
|-------|-----------|--------|
| `/equity` | Custom inline page (748 lines, ~12 inline components) | Existing — full NLH equity UI |
| `/equity/plo` | VariantEquityPage shared component | Scaffolded — needs visual polish |
| `/equity/stud` | Custom page with `StudHandDisplay` | **Live** — 7-card visual, equity API |
| `/equity/stud8` | Custom page with `StudHandDisplay` | **Live** — same component as stud |
| `/equity/razz` | Custom page with `StudHandDisplay` | **Live** — same component as stud |
| `/equity/badugi` | Custom page with `BadugiHandDisplay` | **Live** — 4-card dark gradient visual |
| `/equity/2-7td` | Functional page, no visual component | **Scaffolded** — waiting meta.ai (5-card draw display) |
| `/equity/2-7sd` | Functional page, no visual component | **Scaffolded** — waiting meta.ai |
| `/icm`, `/train`, `/analyze`, `/play`, `/study`, `/practice` | Various custom pages | Existing |

### Frontend Patterns Discovered:
- **Theme**: `gtoTheme` object from `@/styles/gto-tokens` — single source for all colors, strategy actions, equity buckets
- **Components**: `@/components/equity/` exports RangeGrid (with CellData type), RangeSelector, EquityChart, EquityBar, EquityHeatmap — their barrel at `index.ts`
- **Styling**: Mix of inline `style={}` objects (equity page, Header) and Tailwind utility classes (home page)
- **Header**: `apps/web/src/components/Header.tsx` — inline-styled, `navTabs` array drives the links, uses emoji badges
- **API lib**: `@/lib/api.ts` — `api.fetch()` generic wrapper, `variantApi.list()/get()/equity()` for variant endpoints
- **Shared VariantEquityPage**: At `apps/web/src/app/equity/variant-page.tsx` — fetches variant info, range inputs, equity calc button, results display

## SSH Tooling for Host File Writes

**Do NOT use** nested heredocs inside double-quoted SSH commands for complex file writes (quoting gets mangled).

**Preferred pattern — python3 /dev/stdin with local heredoc:**
```bash
ssh -o StrictHostKeyChecking=no -i /home/hermeswebui/.hermes/home/.ssh/id_ed25519 sc@172.19.0.1 'python3 /dev/stdin' << 'PYEOF'
import pathlib
p = pathlib.Path("/home/sc/repos/gto-wizard-clone/apps/web/src/app/equity/variant-page.tsx")
p.write_text("""... file content ...""")
print("OK")
PYEOF
```

**Fallback — pipe local file to SSH python:**
```bash
cat /workspace/my_script.py | ssh -o StrictHostKeyChecking=no -i /home/hermeswebui/.hermes/home/.ssh/id_ed25519 sc@172.19.0.1 'python3 -c "import sys; exec(sys.stdin.read())"'
```

**scp does NOT work** from the WebUI container — SSH key path differs from scp expectations. Always use SSH + stdin piping for file transfers.

## Git Workflow
- SSH into host: `ssh -o StrictHostKeyChecking=no -i /home/hermeswebui/.hermes/home/.ssh/id_ed25519 sc@172.19.0.1`
- Work in `/home/sc/repos/gto-wizard-clone`
- Commit with conventional commits (`feat:`, `fix:`, `chore:`)
- **Always unstage build artifacts before committing**: `git restore --staged apps/web/.turbo/ apps/web/public/`
- Keep `apps/web/src/app/equity/page.tsx` as reference for NLH UI patterns

## API Integration
- List variants: `GET /api/v1/variants` → `variantApi.list()`
- Get variant: `GET /api/v1/variants/{key}` → `variantApi.get(key)`
- Calculate equity: `POST /api/v1/variants/{key}/equity` with `{ hero_range, villain_range, board, iterations }` body → `variantApi.equity(key, hero, villain, board, iterations)`
- All equity routes live under FastAPI backend on port 8000
- Equity response shape: `{ hero_equity: float, villain_equity: float | null, iterations: int, variant: string, variant_name: string }`

## HTML-to-React Conversion Patterns

When the user returns HTML output from meta.ai, convert it using these specific patterns:

### Card Component Pattern (face-up/down)
```tsx
// Face-down card — no content, patterned background
function FaceDownCard() {
  return (
    <div style={{
      width: 80, height: 112, borderRadius: 8, flexShrink: 0,
      background: "#2d3748",
      backgroundImage: `repeating-linear-gradient(45deg, #252f40 0px, #252f40 3px, #2d3748 3px, #2d3748 6px, #344054 6px, #344054 9px, #2d3748 9px, #2d3748 12px)`,
      border: "1.5px solid #4a5568",
      boxShadow: `inset 0 1px 2px rgba(255,255,255,0.05), inset 0 -1px 3px rgba(0,0,0,0.5), 0 6px 12px rgba(0,0,0,0.5)`,
    }}>
      <div style={{
        position: "absolute", inset: 6, borderRadius: 4,
        border: "1px solid rgba(255,255,255,0.05)",
        backgroundImage: `repeating-linear-gradient(-45deg, transparent, transparent 4px, rgba(0,0,0,0.15) 4px, rgba(0,0,0,0.15) 5px)`,
      }} />
    </div>
  );
}

// Face-up card — absolute-positioned rank/suit
function FaceUpCard({ rank, suit }: { rank: string; suit: string }) {
  const isRed = suit === 'h' || suit === 'd';
  const sym = { h: '♥', d: '♦', c: '♣', s: '♠' }[suit] || suit;
  return (
    <div style={{
      width: 80, height: 112, borderRadius: 8, flexShrink: 0,
      background: "#f7fafc", border: "1.5px solid #1a202c",
      color: isRed ? "#e53e3e" : "#1a202c", position: "relative",
      boxShadow: `0 6px 12px rgba(0,0,0,0.5)`,
    }}>
      <span style={{ position: "absolute", top: 6, left: 7, fontSize: 15, fontWeight: 800, fontFamily: "'SF Mono', monospace" }}>
        {rank}
      </span>
      <span style={{ position: "absolute", top: "50%", left: "50%", transform: "translate(-50%, -50%)", fontSize: 38 }}>
        {sym}
      </span>
      <span style={{ position: "absolute", bottom: 6, right: 7, fontSize: 15, fontWeight: 800, transform: "rotate(180deg)" }}>
        {rank}
      </span>
    </div>
  );
}
```

### Key Conversion Rules

| meta.ai CSS | React Equivalent |
|-------------|------------------|
| `display: flex; gap: 14px;` | `style={{ display: "flex", gap: 14 }}` |
| `::before` / `::after` pseudo-elements | Separate `<div>` with absolute positioning |
| `background-image: repeating-linear-gradient(...)` | `style={{ backgroundImage: \`repeating-linear-gradient(...)\` }}` |
| `@media (max-width: 780px) { .card { width: 68px; } }` | **Skip in component** — use Tailwind responsive classes or CSS-in-JS media queries are not needed since the component is responsive by itself via %/vw units |
| `user-select: none` → `userSelect: "none"` (camelCase inline styles) |
| `box-shadow: ..., ..., ...` → `style={{ boxShadow: \`..., ..., ...\` }}` (template literal) |
| `transform: rotateX(10deg)` → `style={{ transform: "rotateX(10deg)", transformStyle: "preserve-3d" }}` |
| `flex-shrink: 0` → `style={{ flexShrink: 0 }}` + `className="shrink-0"` (both) |

### When to Use Inline Styles vs Tailwind

**Use inline styles when:**
- CSS gradients (card patterns, felt vignettes, divider glow)
- Multiple box-shadows with inset
- CSS transforms with perspective
- Dynamic values (card colors based on suit, equity color based on value)

**Use Tailwind when:**
- Layout (flex, grid, padding, margin, gap)
- Typography (text size, weight, color)
- Positioning (absolute, relative, z-index)
- Hover/transition effects (transition-colors, hover:bg-*)
- Responsive containers (max-w-*, mx-auto)

### The Helper Function Pattern

After creating a visual component, always create a helper that maps API data → component props:

```tsx
export function makeDefaultStudHand(
  upCards: Array<{ rank: string; suit: string }>,
  equity: number, name: string, isHero: boolean
): StudPlayerData {
  const cards = [
    { faceUp: false }, { faceUp: false },
    ...upCards.slice(0, 4).map(c => ({ rank: c.rank, suit: c.suit, faceUp: true })),
    { faceUp: false },
  ];
  while (cards.length < 7) cards.push({ faceUp: false });
  return { name, cards: cards.slice(0, 7), equity, isHero };
}
```

### Component File Organization
```
components/<variant>/
├── index.ts          — Barrel export
└── <Component>.tsx   — Main component + types + helper fns
```

### Build Verification
After wiring a new component:
```bash
cd /home/sc/repos/gto-wizard-clone/apps/web
npx next build 2>&1 | tail -10
```
Expect to see new routes listed with size. If build fails, check: missing imports, type mismatches, unescaped JSX special characters.

### Staging Safety
```bash
# Before commit, always unstage build artifacts:
git restore --staged apps/web/.turbo/ apps/web/public/
```

### Prompt Design for meta.ai

Effective meta.ai prompts follow this structure:
1. **Component name** — "Badugi hand display component"
2. **What NOT to include** — "Don't make it a full page — just the card area"
3. **Layout** — "Two players: Hero (bottom) and Villain (top)"
4. **Card structure** — "Each player has N card slots" + "all face-up" or "first 2 face-down"
5. **Visual constraints** — "Use rank symbols (A, K, Q, ...) and suit symbols (♠ ♥ ♦ ♣)"
6. **State to show** — "Show player name and equity percentage below each hand"
7. **Theme** — "Background: dark green felt (#1a1a2e)"
8. **Format** — "Generate as self-contained HTML with inline CSS"

## UI Work Remaining (candidates for meta.ai):
1. **Stud equity page** — **DONE** (uses StudHandDisplay component)
2. **Razz equity page** — **DONE** (uses StudHandDisplay component, same 7-card layout)
3. **Badugi equity page** — **DONE** (uses BadugiHandDisplay component, 4-card dark gradient)
4. **Draw equity page** (2-7 TD/SD) — 5-card display with discard interface (prompt saved in .meta-ui-prompts.md)
5. Range selector refinements — current grid is functional but not polished
6. Training quiz UIs — card flip animations, progress indicators, results
7. Hand viewer — street-by-street playback with bet sizing visuals
