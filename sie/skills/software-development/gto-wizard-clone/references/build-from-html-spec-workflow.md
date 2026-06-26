# Build from Raw HTML/CSS/JS Spec — Workflow

## When the user provides HTML/CSS/JS as a spec

The user may share a complete HTML file that represents the EXACT UI they want. This IS the design spec — treat it as the canonical source of truth for structure, spacing, colors, font sizes, interactive behavior, and layout.

## Conversion Process

### Step 1: Parse the HTML spec

Read the file and identify:
- **CSS :root variables** → these become the design token system
- **Container structure** → the component hierarchy (nav → sidebar → main → panels)
- **Interactive states** → JS event handlers, tab switching, modal open/close, chip toggles
- **Media queries** → responsive breakpoints and layout changes

### Step 2: Create design tokens

Extract all `var(--xxx)` values and repeated hex codes:

```
--bg: #0e0e0f     → gto.colors.bg
--panel: #1a1c1e  → gto.colors.panel
--border: #2a2e32 → gto.colors.border
--teal: #00b894   → gto.colors.teal
...
```

Export as a typed constants object in `styles/<project>-tokens.ts`.

### Step 3: Convert HTML to JSX

Rules:
- `class` → `className`
- `style="..."` → `style={{...}}` with JS object syntax
- Inline event handlers (`onclick=...`) → React `onClick={...}`
- `for` → `htmlFor`
- SVG attributes (`stroke-width` → `strokeWidth`, `fill-rule` → `fillRule`)
- Self-closing tags (`<br>` → `<br/>`)
- Template literals in CSS: no change needed in React inline styles

### Step 4: Extract interactive JS

The spec's `<script>` block contains:
- Modal open/close handlers → React state (`const [modalOpen, setModalOpen]`)
- Tab switching → `const [activeTab, setActiveTab]`
- Chip toggles → `const [selectedChip, setSelectedChip]`
- View switching (setup→training) → `const [showTraining, setShowTraining]`
- Matrix generation → React array state, not DOM manipulation

**Replace `document.getElementById` with React state.** Never use `document.querySelector` in React.

### Step 5: Style mapping

CSS inline styles convert 1:1 to React inline styles. Example:

```html
<div style="display:flex;flex-direction:column;height:100vh;background:var(--bg)">
```
→
```tsx
<div style={{display:"flex",flexDirection:"column",height:"100vh",background:"#0e0e0f"}}>
```

CSS classes (from `<style>` block) convert to inline styles for pixel-exact control. Tailwind classes are NOT needed — the spec already has the exact styling.

### Step 6: Verify against spec

After the page renders, compare against the spec HTML:
- Colors match the spec's hex values
- Spacing matches (padding, margin, gap)
- Font sizes match
- Component tree structure matches (same nesting, same elements)
- Interactive behavior works (modals open, tabs switch, chips toggle)

## Key Differences from Regular UI Development

| Regular | Spec-Based |
|---------|------------|
| Estimate layout from screenshots | Layout is EXACTLY defined in HTML |
| Choose colors manually | Colors are in CSS `:root` / inline styles |
| Guess font sizes | Font sizes are in the spec |
| Build interactive state from scratch | Interactive code is in `<script>` block |
| Approximate responsive behavior | Media queries are in `<style>` block |
| Try Tailwind classes until it looks right | Write inline styles that match the spec exactly |

## Example: 700-line HTML spec → React

The training page (June 2026) was rebuilt from a complete HTML/CSS/JS spec. The spec had:
- 200 lines of CSS in `<style>` (design system + layout + responsive)
- 450 lines of HTML (nav + setup view + training view + modal)
- 80 lines of JS (interactive handlers + matrix generation)

The React conversion was ~32KB of TSX. The process took ~10 minutes of file writing and produced a page that matched the spec exactly on first render.
