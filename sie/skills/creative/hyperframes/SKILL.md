---
name: hyperframes
description: Create HTML-based video compositions, animated title cards, social overlays, captioned talking-head videos, audio-reactive visuals, and shader transitions using HyperFrames. HTML is the source of truth for video. Use when the user wants a rendered MP4/WebM from an HTML composition, wants to animate text/logos/charts over media, needs captions synced to audio, wants TTS narration, or wants to convert a website into a video.
version: 1.1.0
author: heygen-com
license: Apache-2.0
platforms: [linux, macos, windows]
prerequisites:
  commands: [node, ffmpeg, npx]
  env: []
metadata:
  hermes:
    tags: [creative, video, animation, html, gsap, motion-graphics]
    related_skills: [manim-video, meme-generation, hyperframes-text-workaround]
    category: creative
    requires_toolsets: [terminal]
---

# HyperFrames

HTML is the source of truth for video. A composition is an HTML file with `data-*` attributes for timing, a GSAP timeline for animation, and CSS for appearance. The HyperFrames engine captures the page frame-by-frame and encodes to MP4/WebM with FFmpeg.

**⚠️ CRITICAL TEXT RENDERING LIMITATION:** GSAP-animated text elements do **not** render in HyperFrames' headless Chrome screenshot capture. After 7+ approaches tested, text controlled by any GSAP opacity/visibility animation (opacity, autoAlpha, fromTo, set/to) consistently fails to appear in captured frames. JS-created DOM elements (graph nodes, shapes) render fine. **For text-heavy compositions, you MUST use the `hyperframes-text-workaround` skill to pre-render text as transparent PNG images and use `<img>` tags instead of text `<div>` elements.**

## ⚠️ Text Rendering Limitation (KNOWN BUG)

HyperFrames' headless Chrome screenshot capture **does not render text elements** controlled by GSAP animations. This affects:
- Text `<div>` elements with GSAP opacity/visibility animations
- Text that fades in/out via GSAP timeline
- Any text whose visibility is controlled by JavaScript

**Workaround:** Use the `hyperframes-text-workaround` skill — pre-render text as PNG images with Python/Pillow, then use `<img>` tags.

**If HyperFrames produces empty/black video:** Fall back to pure Python/PIL + FFmpeg (see `hyperframes-text-workaround` for details).

- User asks for a rendered video from text, a script, or a website
- Animated title cards, lower thirds, or typographic intros
- Captioned narration video (TTS + captions synced to waveform)
- Audio-reactive visuals (beat sync, spectrum bars, pulsing glow)
- Scene-to-scene transitions (crossfade, wipe, shader warp, flash-through-white)
- Social overlays (Instagram/TikTok/YouTube style)
- Website-to-video pipeline (capture a URL, produce a promo)
- Any HTML/CSS/JS animation that must render deterministically to a video file

Do **not** use this skill for:
- Pure math/equation animation (→ `manim-video`)
- Image generation or memes (→ `meme-generation`, image models)
- Live video conferencing or streaming

## Quick Reference

```bash
npx hyperframes init my-video               # scaffold a project
cd my-video
npx hyperframes lint                        # validate before preview/render
npx hyperframes preview                     # live-reload browser preview (port 3002)
npx hyperframes render --output final.mp4   # render to MP4
npx hyperframes doctor                      # diagnose environment issues
```

Render flags: `--quality draft|standard|high` · `--fps 24|30|60` · `--format mp4|webm` · `--docker` (reproducible) · `--strict`.

Full CLI reference: [references/cli.md](references/cli.md).

## Text Rendering Workaround

**This is the most common pitfall.** If your composition has text that needs to appear/disappear or animate:

1. **Do NOT** use text `<div>` elements with GSAP opacity animations — they won't render
2. **Do NOT** use CSS `opacity:0`/`visibility:hidden` with GSAP to toggle — won't render
3. **DO** pre-render all text as transparent PNG images using the `hyperframes-text-workaround` skill
4. **DO** use `<img src="text_images/name.png" class="clip" data-start="X" data-duration="Y" />` tags
5. HyperFrames' native clip system (`data-start`/`data-duration`) works on `<img>` tags without GSAP
6. Keep GSAP only for non-text animations (graph nodes, particles, panel transitions)

See `hyperframes-text-workaround` skill for complete Python/Pillow code to generate text images.

## Setup (one-time)

```bash
bash "$(dirname "$(find ~/.hermes/skills -path '*/hyperframes/SKILL.md' 2>/dev/null | head -1)")/scripts/setup.sh"
```

## Environment Requirements

- Node.js >= 22
- FFmpeg (in PATH)
- Chrome/Chromium for capture (puppeteer headless shell)
- System libraries for headless Chrome: `libglib-2.0.so.0`, `libnss3`, `libnspr4`, `libatk1.0-0`, `libatk-bridge2.0-0`, `libdbus-1-3`, `libx11-6`, `libxcomposite1`, `libxdamage1`, `libxext6`, `libxfixes3`, `libxrandr2`, `libgbm1`, `libpango-1.0-0`, `libcairo2`, `libasound2`

**Arch Linux note:** `lsof` is not available by default. Use `fuser PORT/tcp` or check `/proc/*/cmdline` for port conflicts. Missing system libs may cause Chrome to fail with exit code 127.

## Procedure

### 1. Plan before writing HTML

### 2. Scaffold

```bash
npx hyperframes init my-video --non-interactive
```

### 3. Layout before animation. Animate with GSAP.

Rules:
- Every timed element needs `data-start`, `data-duration`, and `data-track-index`
- GSAP timelines must be paused and registered on `window.__timelines`
- Videos use `muted` with a separate `<audio>` element
- Only deterministic logic — no `Date.now()`, no `Math.random()` (use seeded PRNG)
- **Text elements: use `<img>` tags with pre-rendered PNGs, not raw text with GSAP**

### 4. Lint, validate, preview, render

```bash
npx hyperframes lint              # catches issues
npx hyperframes render --quality draft --output draft.mp4    # fast iteration
npx hyperframes render --quality high --output final.mp4     # final delivery
```
