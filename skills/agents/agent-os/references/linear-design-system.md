# Linear Dark Design System (agent-os Dashboard)

Based on Linear.app's visual language. Applied to the agent-os dashboard frontend
(`/opt/data/agent-os/apps/dashboard/frontend`) as a dark-mode-first design refresh.

## When to Use

Use Linear design tokens when building or refreshing dashboard UI components.
The goal is ultra-minimal product UI — no gradients for decoration, no glassmorphism
unless functional, tight typography, purposeful whitespace.

## Color Palette

```css
/* Canvas */
--background-base: #08090a;       /* Near-black page background */
--background-raised: #0c0c0e;    /* Card/surface background */
--background-overlay: #111115;   /* Modal/dropdown backgrounds */

/* Borders */
--border-subtle: rgba(255, 255, 255, 0.06);   /* Card borders, dividers */
--border-default: rgba(255, 255, 255, 0.10);  /* Input borders, separators */
--border-strong: rgba(255, 255, 255, 0.18);   /* Focused borders, emphasis */

/* Brand — Linear indigo */
--color-primary: #5e6ad2;         /* Primary buttons, links, brand elements */
--color-primary-hover: #6b7ae8;   /* Hover state */
--color-primary-muted: rgba(94, 106, 210, 0.15); /* Badge backgrounds, highlights */

/* Accent — violet + warm glow */
--color-accent: #7170ff;          /* Accent elements, active states */
--color-warm-glow: #ff6b35;       /* Warm orange glow for ambient effects */

/* Text */
--text-primary: #e8e6e3;          /* Primary text — warm white */
--text-secondary: #8a8f98;        /* Secondary/muted text */
--text-tertiary: #5c6370;         /* Placeholder, disabled text */

/* Status */
--color-success: #10b981;         /* Green — healthy, low CPU */
--color-warning: #f59e0b;         /* Amber — warning, 50-80% CPU */
--color-danger: #eb4545;          /* Red — error, >80% CPU */

/* Input/output token colors (warm/cool) */
--text-input: #ffe6cb;            /* Input token counts — warm amber */
--text-output: #6beb8d;            /* Output token counts — cool green */
```

## Typography

```css
/* Font family — Inter variable */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Scale */
--font-sans: 'Inter', ui-sans-serif, system-ui, sans-serif;
font-size: 13px;       /* Body text */
font-size: 11px;       /* Small labels, metadata */
font-size: 10px;       /* Micro labels, badges */
font-size: 9px;        /* Minimum readable */

/* Weight */
font-weight: 500;      /* Medium — most UI text */
font-weight: 600;      /* Semibold — section headers */
font-weight: 400;      /* Regular — secondary text */
```

## Layout & Spacing

```css
/* Card radius */
border-radius: 6px;    /* All cards, buttons, inputs */

/* Spacing scale (Tailwind custom-values in tailwind.config.js) */
--space-1: 2px;
--space-2: 4px;
--space-3: 8px;
--space-4: 12px;
--space-6: 16px;
--space-8: 24px;
```

## Key Component Patterns

### Card
```tsx
<div className="bg-[#0c0c0e] border border-[rgba(255,255,255,0.06)] rounded-xl p-4">
```

### Inline badge
```tsx
<span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium
  bg-[rgba(94,106,210,0.15)] text-[#5e6ad2]">
```

### Muted text
```tsx
<span className="text-[#8a8f98] text-[10px]">label</span>
```

### Pulsing live indicator
```tsx
<span className="h-1.5 w-1.5 rounded-full bg-[#10b981] animate-pulse" />
```

### CPU Sparkline (Unicode)
```tsx
const sparkline = cpuHistory.map(s => {
  const h = Math.round((parseFloat(s.cpu_percent) / sparkMax) * 7);
  return '▁▂▃▄▅▆▇'[h];  // 8 levels
}).join('');
// Color: #10b981 (<50%), #f59e0b (50-80%), #eb4545 (>80%)
```

### Token counter display
```tsx
// Per-message tokens
<span className="text-[10px] text-[#8a8f98] ml-2 shrink-0">{n} tokens</span>

// Session total
<span className="text-[10px] text-[#8a8f98] shrink-0">{input + output} tokens</span>
```

## shadcn/ui @theme inline Tokens

The dashboard uses Tailwind v4 with `@theme inline` — CSS custom properties
cascade through all components without explicit class overrides:

```css
@theme inline {
  --color-background: var(--background-base);
  --color-foreground: var(--text-primary);
  --color-border: var(--border-default);
  --color-primary: var(--color-primary);
  --color-secondary: var(--background-raised);
  --color-muted: var(--text-secondary);
  --color-accent: var(--color-accent);
  --color-destructive: var(--color-danger);
  --color-success: var(--color-success);
  --color-warning: var(--color-warning);
  /* ... */
}
```

## Adding a New Theme Variant

1. Add Linear tokens to `index.css` under `:root[data-theme="linear"]`
2. Update `themes/index.tsx` — add Linear to `THEMES` array with palette
3. For optional palette: always provide `??` fallback to Linear defaults
```tsx
const palette = preset.palette ?? {
  background: { hex: '#08090a' },
  midground: { hex: '#111115' },
  warmGlow: '#7170ff'
};
```

## Linear vs Previous (Hermes Teal) Theme

| Element | Linear | Hermes (old) |
|---|---|---|
| Background | #08090a | #0f1118 |
| Brand | #5e6ad2 indigo | #14b8a6 teal |
| Text | #e8e6e3 warm-white | #f7f8f8 cool-white |
| Border | rgba(255,255,255,0.06) | rgba(255,255,255,0.08) |
| Card radius | 6px | 8px |
