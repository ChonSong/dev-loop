# Single-File Multi-Panel Compositions

When building a video with multiple scenes/panels in a single HTML file (rather than separate sub-composition files), follow these rules to satisfy the HyperFrames linter and avoid rendering issues.

## Pattern

```html
<body data-composition-id="main" data-duration="95" data-width="1920" data-height="1080">

  <!-- Panel 1: visible 0-30s -->
  <div id="panel-1" data-composition-id="panel-1" data-width="1920" data-height="1080"
       style="position:absolute;top:0;left:0;width:100%;height:100%;background:#0a1628;">
    <div id="p1-title" class="clip" data-start="0" data-duration="6" data-track-index="1">...</div>
    <div id="p1-sub" class="clip" data-start="7" data-duration="6" data-track-index="1">...</div>
  </div>

  <!-- Panel 2: visible 30-60s -->
  <div id="panel-2" data-composition-id="panel-2" data-width="1920" data-height="1080"
       style="position:absolute;top:0;left:0;width:100%;height:100%;background:#1a1a2e;opacity:0;visibility:hidden;">
    <div id="p2-title" class="clip" data-start="0" data-duration="5" data-track-index="3">...</div>
  </div>

  <!-- Transitions -->
  <div id="trans-1-2" style="position:absolute;top:0;left:0;width:100%;height:100%;z-index:100;opacity:0;pointer-events:none;background:#fff;"></div>

  <script>
    window.__timelines = window.__timelines || {};
    const tl = gsap.timeline({ paused: true });

    // Kill all clips (lint requires this pattern)
    document.querySelectorAll('.clip').forEach(el => {
      const start = parseFloat(el.dataset.start || 0);
      const dur = parseFloat(el.dataset.duration || 5);
      tl.set(el, { opacity: 0, visibility: 'hidden' }, start);
      tl.set(el, { opacity: 1, visibility: 'visible' }, start + 0.01);
      tl.set(el, { opacity: 0, visibility: 'hidden' }, start + dur + 0.01);
    });

    // Panel visibility windows
    tl.set('#panel-1', { opacity: 1, visibility: 'visible' }, 0);
    tl.set('#panel-1', { opacity: 0, visibility: 'hidden' }, 29);
    tl.set('#panel-2', { opacity: 1, visibility: 'visible' }, 29);
    tl.set('#panel-2', { opacity: 0, visibility: 'hidden' }, 59);

    // Transition: crossfade
    tl.to('#panel-1', { opacity: 0, duration: 1, ease: 'power2.inOut' }, 28.5);
    tl.fromTo('#panel-2', { opacity: 0 }, { opacity: 1, duration: 1, ease: 'power2.inOut' }, 28.5);

    window.__timelines['main'] = tl;
  </script>
</body>
```

## Rules

1. **Every panel div needs `data-composition-id`, `data-width`, `data-height`** — the lint flags any container of `.clip` elements that lacks these.

2. **Each panel uses a unique `data-track-index` range** — the lint checks ALL clips globally. Panel 1 uses track 1, panel 2 uses track 3, panel 3 uses track 5. Never reuse track indices across panels.

3. **Clip `data-start` times are relative to the composition (0-based)**, not to the panel's visibility window. Keep clip starts within the panel's visibility duration.

4. **Panel visibility is controlled by GSAP**, not by clip timing. The master timeline sets `opacity: 0; visibility: hidden` on panels outside their window.

5. **Transitions go in their own divs** with `z-index: 100` and `pointer-events:none`. Animate their opacity in the master timeline.

6. **Use `Math.floor` for repeat calculations**, not `Math.ceil`.

7. **Use a seeded PRNG** instead of `Math.random()` — mulberry32 with a fixed seed.

8. **System fonts only for render reliability** — Google Fonts `<link>` tags may fail in sandboxed/offline renders.
