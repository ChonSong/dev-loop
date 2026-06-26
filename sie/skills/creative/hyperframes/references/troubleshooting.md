# Troubleshooting

## `HeadlessExperimental.beginFrame' wasn't found` (first thing to check)

**Symptom:** `npx hyperframes render` fails with:

```
✗ Render failed
Protocol error (HeadlessExperimental.beginFrame):
'HeadlessExperimental.beginFrame' wasn't found
```

**Cause:** Chromium 147+ removed the `HeadlessExperimental.beginFrame` CDP command. This affected sandbox environments (e.g., OpenClaw, some containerized agent hosts) that ship modern Chromium as the system browser. See [hyperframes#294](https://github.com/heygen-com/hyperframes/issues/294).

**Fix (permanent — preferred):** upgrade.

```bash
npx hyperframes upgrade -y
# or
npm install -g hyperframes@latest
```

`hyperframes >= 0.4.2` auto-detects whether the resolved browser supports `beginFrame` (checks for `chrome-headless-shell` in the binary path) and falls back to screenshot capture mode when it doesn't. Commit [`4c72ba4`](https://github.com/heygen-com/hyperframes/commit/4c72ba4a36ec2bd6733f7b9cb2a9e63f9fb234b9) (March 2026) shipped this auto-detect.

**Fix (escape hatch — if you can't upgrade):**

```bash
export PRODUCER_FORCE_SCREENSHOT=true
npx hyperframes render
```

This forces screenshot mode regardless of the binary. Screenshot mode is slightly slower but visually identical.

**Fix (prevent — recommended):** install `chrome-headless-shell` so the engine can use the fast BeginFrame path:

```bash
npx puppeteer browsers install chrome-headless-shell
# or let the CLI do it
npx hyperframes browser --install
```

`scripts/setup.sh` runs this automatically.

## `npx hyperframes render` hangs for 120s then times out

**Cause:** the resolved browser is system Chrome (e.g., `/usr/bin/google-chrome`) and doesn't support the BeginFrame path, but auto-detect also missed it (older `hyperframes` version).

**Fix:**
1. Check which binary is being used: `npx hyperframes browser --path`
2. If it's system Chrome, either:
   - Install `chrome-headless-shell`: `npx hyperframes browser --install`, OR
   - Set the escape hatch: `export PRODUCER_FORCE_SCREENSHOT=true`, OR
   - Upgrade: `npx hyperframes upgrade -y`

## `ffmpeg: command not found`

Install FFmpeg via your system package manager:

| OS / distro     | Command                             |
| --------------- | ----------------------------------- |
| Ubuntu / Debian | `sudo apt-get install -y ffmpeg`    |
| Fedora / RHEL   | `sudo dnf install -y ffmpeg`        |
| Arch            | `sudo pacman -S ffmpeg`             |
| macOS           | `brew install ffmpeg`               |
| Windows         | `winget install Gyan.FFmpeg`        |

Verify: `ffmpeg -version`.

## `Node version X is not supported`

HyperFrames requires Node.js >= 22. Check with `node --version`.

- **nvm:** `nvm install 22 && nvm use 22`
- **Homebrew (macOS):** `brew install node@22 && brew link --overwrite node@22`
- **apt:** follow [nodesource](https://github.com/nodesource/distributions) for Node 22 LTS.

## `ENOSPC: no space left on device` or OOM kills during render

Renders are memory- and disk-hungry. Minimums:

- **RAM:** 4 GB free (8 GB recommended for 60fps / `--quality high`)
- **Disk:** 2 GB free scratch space — frames are written to `/tmp` during capture

Mitigations:
- Lower quality: `--quality draft`.
- Lower fps: `--fps 24`.
- Lower worker count: `--workers 1`.
- Set `TMPDIR` to a volume with more space: `export TMPDIR=/mnt/scratch`.

## Lint passes but the render is blank / black frames

Check the browser console in `preview` — usually:
- A timeline was registered with the wrong key (`__timelines["typo"]` instead of `__timelines["root"]`).
- The root composition was wrapped in `<template>` (only sub-compositions use `<template>`).
- A script tag failed to load — check Network tab in preview.

Run `npx hyperframes lint --verbose` to see info-level findings.

## Text clips are invisible in render (graph nodes show, but no text)

**Symptom:** Rendered video shows the knowledge graph nodes/edges but all text elements (titles, quotes, labels) are invisible. Frame captures from the MP4 show only the background and graph nodes.

**Cause:** The `.clip` CSS class has `opacity: 0` set in `<style>`, AND the GSAP timeline also tries to control opacity. The HyperFrames capture engine reads `window.__timelines` and plays it back, but the CSS `opacity: 0` rule on `.clip` takes precedence over the inline styles that GSAP sets, making text permanently invisible during capture.

**Fix:** Remove `opacity: 0` from the `.clip` CSS rule. Instead, control clip visibility entirely through the GSAP timeline:
```css
/* DON'T do this: */
.clip { opacity: 0; }

/* DO this: leave .clip empty or remove it entirely */
.clip { }
```

Then in your timeline setup, explicitly hide all clips at time 0 and animate them in/out:
```javascript
document.querySelectorAll('.clip').forEach(function(el) {
  var start = parseFloat(el.dataset.start || 0);
  var dur = parseFloat(el.dataset.duration || 5);
  tl.set(el, { opacity: 0 }, 0);                          // hidden at t=0
  tl.to(el, { opacity: 1, duration: 0.6, ease: 'power2.out' }, start);  // fade in
  tl.to(el, { opacity: 0, duration: 0.4, ease: 'power2.in' }, start + dur - 0.2); // fade out
});
```

**Key principle:** In HyperFrames, the GSAP timeline registered on `window.__timelines["composition-id"]` is the single source of truth for clip visibility. Don't fight it with CSS opacity rules.

## Contrast warnings from `hyperframes validate`

```
⚠ WCAG AA contrast warnings (3):
  · .subtitle "secondary text" — 2.67:1 (need 4.5:1, t=5.3s)
```

- **Dark backgrounds:** brighten the failing color until it clears 4.5:1 (normal text) or 3:1 (large text — 24px+ or 19px+ bold).
- **Light backgrounds:** darken it.
- Stay within the palette family — don't invent a new color, adjust the existing one.
- Skip the check temporarily with `--no-contrast` if iterating rapidly, but clear it before delivery.

## `Font family 'X' not supported by compiler`

The compiler embeds a curated set of web-safe + open-source fonts. If a font isn't supported, either:
- Swap to a supported alternative from the warning.
- Register a custom font via `@font-face` pointing to a `.woff2` in the project directory (the compiler embeds referenced `@font-face` files).

## Video plays back muted or with no audio

Check:
- The `<video>` element has `muted playsinline` (required — browser autoplay policy).
- Audio is a **separate** `<audio>` element, not the video element.
- Audio `data-volume` is set (defaults to 1).
- The audio file is at the expected path — compositions load relative to their own directory.

## Chrome headless shell fails with `libglib-2.0.so.0: cannot open shared object file`

**Symptom:** `npx hyperframes render` fails with:
```
Failed to launch the browser process: Code: 127
stderr: ... chrome-headless-shell: error while loading shared libraries: libglib-2.0.so.0
```

**Cause:** The puppeteer-bundled `chrome-headless-shell` binary depends on system shared libraries (glib, nss, atk, dbus, X11, etc.) that are not installed in the container/VM.

**Fix:** Point `LD_LIBRARY_PATH` at a directory containing the needed `.so` files. In this environment, pre-extracted libs live at:
```bash
export LD_LIBRARY_PATH="/home/hermeswebui/.local/chrome-libs/usr/lib/x86_64-linux-gnu:/home/hermeswebui/.local/chrome-libs/lib:${LD_LIBRARY_PATH}"
```
Verify with: `ldd $(npx hyperframes browser --path) | grep "not found"` — should return zero lines.

**Also ensure `npx` and `ffmpeg` are in PATH** when running from a script or background shell (which may not source `.bashrc`):
```bash
export PATH="/home/hermeswebui/.hermes/home/.local/bin:/home/hermeswebui/.hermes/local/bin:/usr/local/bin:/usr/bin:/bin:${PATH}"
```

## Single-file multi-panel compositions: lint requires `data-composition-id` on every clip container

**Symptom:** `npx hyperframes lint --strict` reports `root_missing_composition_id` on a div that is NOT intended as a sub-composition — it's just a visual panel container.

**Cause:** The lint scans the DOM for any element containing `.clip` children. If that element lacks `data-composition-id`, it flags it as a missing root composition ID. This happens when you build a single-file multi-panel composition where each panel div wraps a group of clips.

**Fix:** Add `data-composition-id`, `data-width`, and `data-height` to every panel div that contains clips, even if it's not a real sub-composition:
```html
<div id="panel-paradise" data-composition-id="panel-paradise" data-width="1920" data-height="1080" style="background:#0a1628;">
  <div id="p-title" class="clip" data-start="0" data-duration="6" data-track-index="1">...</div>
</div>
```

**Also:** Each panel's clips must use **unique `data-track-index` values** that don't overlap with other panels. The lint checks all clips globally, not per-panel. If paradise clips use track 1, earth clips should use track 3, hell clips track 5, etc. Clips on the same track cannot overlap in their `data-start`/`data-duration` windows even if they're in different panels that are never visible simultaneously.

## `npx` not found in background/ssh shells

**Symptom:** `npx: command not found` when running render scripts via `bash script.sh`, `ssh`, or `terminal(background=true)`.

**Cause:** These shells don't source `.bashrc` or `.profile`, so the Hermes-local bin directory isn't in PATH.

**Fix:** Always set PATH explicitly in render scripts:
```bash
export PATH="/home/hermeswebui/.hermes/home/.local/bin:/home/hermeswebui/.hermes/local/bin:${PATH}"
```

## Docker render fails on Linux with rootless Docker

Add `--privileged` or pass `--cap-add=SYS_ADMIN`:

```bash
npx hyperframes render --docker --docker-args "--cap-add=SYS_ADMIN"
```

The headless browser needs namespace permissions for sandboxing.

## Bug reports

Include `npx hyperframes info` output + the full error log. File at [github.com/heygen-com/hyperframes](https://github.com/heygen-com/hyperframes/issues).
