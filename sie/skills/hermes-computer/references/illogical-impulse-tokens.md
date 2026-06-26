# Illogical Impulse Design Tokens

Source: end-4/dots-hyprland (14.4k stars) — "illogical-impulse" style
Translated to: Svelte 5 + Tailwind CSS + `@theme` directive

## Colors

```css
--color-bg-deep: #0a0a0f
--color-bg-primary: #12121a
--color-bg-secondary: #16161e
--color-bg-overlay: #1c1c28
--color-accent: #8b5cf6 (purple-500)
--color-accent-light: #c4b5fd (purple-300)
--color-accent-glow: rgba(139, 92, 246, 0.15)
--color-border: rgba(255, 255, 255, 0.10)
--color-border-active: rgba(139, 92, 246, 0.50)
--color-text: #e2e8f0 (gray-100)
--color-text-muted: #9ca3af (gray-400)
--color-text-dim: #6b7280 (gray-500)
```

## Background

```html
<!-- Deep radial gradient -->
<div class="fixed inset-0 -z-20 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-[#1a0a2e] via-[#0a0a0f] to-[#0a0a0f]">
```

## Glassmorphism Panel

```html
<!-- Default panel -->
<div class="backdrop-blur-2xl bg-[#12121a]/80 border border-white/10 rounded-2xl shadow-panel">

<!-- Active/focused panel -->
<div class="backdrop-blur-2xl bg-[#12121a]/90 border-purple-500/30 rounded-2xl ring-1 ring-purple-500/20 shadow-glow">
```

## Shadows (Tailwind @theme)

```css
@theme {
  --shadow-panel: 0 8px 32px rgba(0, 0, 0, 0.4);
  --shadow-glow: 0 0 20px rgba(139, 92, 246, 0.15);
}
```

## Corner Radius

- All panels: `rounded-2xl` (16px)
- Pills/dock: `rounded-full` (9999px)
- Buttons: `rounded-xl` (12px)
- Badges: `rounded-full` (9999px)

## Dock / Status Bar

```html
<!-- Centered floating dock at bottom -->
<div class="fixed bottom-4 left-1/2 -translate-x-1/2 z-50
  flex items-center gap-2
  backdrop-blur-xl bg-[#16161e]/90 border border-white/10
  rounded-full px-4 py-2 shadow-panel">
  <button class="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20
    text-purple-400 hover:text-purple-300 transition-colors">
    <!-- icon -->
  </button>
</div>
```

## Workspace Pill

```html
<!-- Top-center workspace indicator -->
<div class="fixed top-3 left-1/2 -translate-x-1/2 z-50
  flex items-center gap-1
  backdrop-blur-xl bg-[#16161e]/90 border border-white/10
  rounded-full px-3 py-1 shadow-panel">
  {#each [1,2,3,4,5,6,7,8,9] as i}
    <div class="w-2 h-2 rounded-full {i === active ? 'bg-purple-400' : 'bg-white/20'}" />
  {/each}
</div>
```

## Animations

```css
@keyframes grain {
  0%, 100% { transform: translate(0, 0); }
  10% { transform: translate(-5%, -10%); }
  /* ... more keyframes */
}

@keyframes pulseGlow {
  0%, 100% { box-shadow: 0 0 0 0 rgba(139, 92, 246, 0.4); }
  50% { box-shadow: 0 0 20px 0 rgba(139, 92, 246, 0.2); }
}
```

## Custom Scrollbar

```css
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(139, 92, 246, 0.3); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(139, 92, 246, 0.5); }
```

## Tailwind Config (CSS-based @theme)

Add to `frontend/src/styles/glass.css`:

```css
@theme {
  --color-bg-deep: #0a0a0f;
  --color-bg-primary: #12121a;
  --color-bg-secondary: #16161e;
  --color-bg-overlay: #1c1c28;
  --color-accent: #8b5cf6;
  --color-accent-light: #c4b5fd;
  --shadow-panel: 0 8px 32px rgba(0, 0, 0, 0.4);
  --shadow-glow: 0 0 20px rgba(139, 92, 246, 0.15);
}
```

## Component Patterns

| Component | Classes |
|-----------|---------|
| Tile (default) | `backdrop-blur-2xl bg-[#12121a]/80 border border-white/10 rounded-2xl` |
| Tile (active) | `border-purple-500/30 ring-1 ring-purple-500/20` |
| Resize handle | `w-0.5 bg-transparent hover:bg-purple-500/50 cursor-col-resize transition-colors` |
| Button | `px-3 py-1.5 bg-white/10 hover:bg-white/20 text-purple-400 rounded-xl` |
| Input | `bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-sm` |
| Badge | `px-2 py-0.5 bg-purple-500/20 text-purple-300 rounded-full text-xs` |
| Overlay | `fixed inset-0 bg-black/60 backdrop-blur-sm` |
