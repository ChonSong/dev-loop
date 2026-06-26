# HyperFrames Text Rendering — Debugging Notes

## Problem
Text elements animated with GSAP opacity/visibility don't appear in HyperFrames MP4 renders.
Graph nodes (JS DOM elements) render fine. Only text is affected.

## Approaches Tested (All Failed)

### Approach 1: CSS opacity:0 + GSAP timeline
```css
.clip { opacity: 0; }
tl.set(el, { opacity: 0 }, 0);
tl.set(el, { opacity: 1 }, start);
tl.set(el, { opacity: 0 }, start + dur);
```

### Approach 2: gsap.fromTo with opacity
```js
tl.fromTo(el, { opacity: 0 }, { opacity: 1, duration: 0.8 }, start);
```

### Approach 3: autoAlpha with timeline
```js
tl.set(el, { autoAlpha: 0 }, 0);
tl.set(el, { autoAlpha: 1 }, start);
```

### Approach 4: CSS visibility:hidden + GSAP autoAlpha override

### Approach 5: Direct gsap.set/to (not on main timeline)

### Approach 6: autoAlpha with fade-out transition

All 6 approaches produced identical results: text invisible in captured frames.

## Root Cause
HyperFrames screenshot capture reads computed DOM styles before GSAP timeline tweens are applied per frame. JS-created absolute-positioned elements (graph nodes) are always visible; text elements need GSAP visibility toggling which isn't captured.

## Workaround
1. Pre-render text as PNG images, use `<img>` elements
2. Use PIL fallback rendering (see references/pil-fallback.md)
