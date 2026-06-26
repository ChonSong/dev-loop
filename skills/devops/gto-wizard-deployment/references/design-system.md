# GTO Wizard Design System (v2 — 2026-06-09)

## CSS Variables

```css
:root {
  --bg: #0b0d0f;           /* Page background — darkest */
  --panel: #14171b;        /* Card/panel background */
  --panel-2: #1a1e23;      /* Secondary panels (sidebar, input bg) */
  --panel-3: #0f1317;      /* Tertiary panels (decision panel bg) */
  --border: #252b32;       /* Borders and dividers */
  --border-light: #303842; /* Subtle borders (hover state) */
  --text: #d1d7df;         /* Primary text */
  --text-muted: #8a94a6;   /* Secondary text, labels */
  --text-dim: #6b7585;     /* Disabled/hint text */
  --accent: #00a98f;       /* Primary accent (buttons, active states) */
  --accent-dark: #007a68;  /* Accent pressed state */
  --red: #e05a5a;          /* Fold, All-in, danger, negative EV */
  --green: #00a67e;        /* Correct, positive EV */
  --orange: #e09b3d;       /* Call, check, medium severity */
}
```

## Typography
- **Font:** Inter, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif
- **Sizes:** 10px (badges), 11px (labels, stats), 12-13px (body, tables), 13.5px (panel tabs), 14-15px (headings), 18-22px (display numbers), 28-34px (odds/equity large)
- **Weights:** 400 (body), 500 (medium emphasis), 600 (semibold), 700 (bold), 800 (display)

## Spacing
- Page padding: 20-24px desktop, 16px mobile
- Panel padding: 14-20px inside panels
- Grid gaps: 16px (desktop), 12px (tablet)
- Border radius: 6px (small inputs), 8px (buttons, cards), 10px (panels), 999px (pills/toggles)

## Component Patterns

### Panel
`background: var(--panel)`, `border: 1px solid var(--border)`, `border-radius: 10px`
Optional gradient: `background: linear-gradient(180deg,#1e1e1e,#1a1a1a)`

### Panel Header
`display: flex`, `justify-content: space-between`, `padding: 11px 14px`, `border-bottom: 1px solid var(--border)`
Active tab: `color: var(--text)`, `border-bottom: 2px solid var(--accent)`

### Pill Button (Toggle/Preset)
`background: #141414`, `border: 1px solid var(--border)`, `border-radius: 999px`
Active: `background: var(--accent-15)`, `border-color: var(--accent)`, `color: var(--accent)`

### Chip (Filter/Label)
`background: var(--panel-2)`, `border: 1px solid var(--border)`, `border-radius: 6px`
Active: `background: var(--accent)`, `color: #02110e`

### Input
`background: #0F0F0F`, `border: 1px solid #2a2a2a`, `border-radius: 8px`, `color: var(--text)`
Focus: `border-color: var(--accent)`, `box-shadow: 0 0 0 3px rgba(0,169,143,.12)`

### Table
Headers: `font-size: 11px`, `color: var(--text-muted)`, `text-transform: uppercase`, `letter-spacing: .05em`
Rows: `border-bottom: 1px solid #1a1a1a`, `padding: 11px 8px`
Hover: `background: #151515`
Active row ("You"): `background: rgba(34,197,94,.06)`, `box-shadow: inset 3px 0 0 var(--accent)`

### Action Bar (Multi-segment)
`height: 6px`, `background: var(--panel-2)`, `border-radius: 3px`, `display: flex`, `overflow: hidden`
Segments: different widths as percentages, each with distinct color

## Layouts

### Two-column
`display: grid`, `grid-template-columns: minmax(0, 1.45fr) minmax(0, 1fr)`, `gap: 16px`
Responsive: `@media (max-width: 1100px) { grid-template-columns: 1fr !important; }`

### Three-column grid
`grid-template-columns: repeat(3, 1fr)`, `gap: 16px`
Responsive → `repeat(2, 1fr)` at 1024px → `1fr` at 700px

### Card Stack (Single column)
Full width cards stacked vertically, 16px gap, optional expand/collapse

## Color Coding by Meaning

| Element | Color | Usage |
|---------|-------|-------|
| Raise/All-in/Bet | `#D32F2F` red | Action buttons, raise range cells |
| Fold | `#3A6EA5` blue | Fold cells, fold ranges |
| Call/Check | `#22c55e` green | Call ranges, correct answers |
| Positive EV | `#00a67e` green | Win amounts, correct answers |
| Negative EV | `#e05a5a` red | Loss amounts, wrong answers |
| Warning | `#e09b3d` orange | Medium severity, check actions |
| Accent | `#00a98f` teal | Primary buttons, active states, highlights |

## States

### Empty
Center-aligned, icon (emoji 48px), heading (18px), description (13px muted), CTA button
```text
Center container: display: flex, flex-direction: column, align-items: center, justify-content: center
Icon: fontSize 48, opacity 0.5
Heading: fontSize 18, color var(--text)
Description: fontSize 13, color var(--text-muted)
```

### Loading
Spinner or skeleton. Centered, muted text.

### Error
Inline error banner at top of relevant section. Red background tint, red text, retry button.

### Active
Element has accent border/shadow, slightly brighter/higher contrast than surrounding elements.
