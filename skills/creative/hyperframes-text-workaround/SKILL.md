---
name: hyperframes-text-workaround
description: Fix for HyperFrames text rendering — pre-render text as PNG images because GSAP-animated text doesn't appear in captured frames
version: 1.0.0
author: OWL
platforms: [linux, macos, metadata]
metadata:
  hermes:
    tags: [creative, video, hyperframes, workaround, text-rendering]
    related_skills: [hyperframes]
    category: creative
---

# HyperFrames Text Rendering Workaround

## Problem
HyperFrames' headless Chrome screenshot capture engine does **not** render text elements that are controlled by GSAP animations. After 7+ approaches confirmed:

- CSS `opacity:0` + GSAP timeline to animate opacity ❌
- `gsap.fromTo()` with opacity keyframes ❌
- `gsap.set()` + `gsap.to()` with opacity ❌
- `autoAlpha` (opacity + visibility) with timeline ❌
- CSS `visibility:hidden` + GSAP `autoAlpha` to show ❌
- Removing all CSS + GSAP clip management ❌

Graph nodes (JS-created DOM elements appended to the DOM) render fine. Raw text elements with any GSAP opacity/visibility animation do **not** appear in captured frames.

## Root Cause
Likely: the headless Chrome capture reads computed styles before GSAP applies its tweens, or the screenshot capture engine doesn't trigger a repaint for GSAP-animated text.

## Solution: Pre-render Text as PNG Images

Use Python/Pillow to generate transparent PNG images of all text, then use `<img>` tags in the composition.

### Step 1: Generate text images

```python
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1920, 720  # Composition dimensions

# Find a usable font
import subprocess
result = subprocess.run(['find', '/usr/share/fonts', '-name', '*.ttf', '-type', 'f'],
                      capture_output=True, text=True, timeout=10)
files = result.stdout.strip().split('\n')
font_path = files[0] if files and files[0] else None

def make_text_image(name, text, size, color, output_dir="text_images"):
    os.makedirs(output_dir, exist_ok=True)
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype(font_path, size * 2)  # 2x for quality
    except:
        font = ImageFont.load_default()
    
    lines = text.split('\n')
    line_heights = []
    line_widths = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        line_widths.append(w)
        line_heights.append(h)
    
    total_h = sum(line_heights) + (len(lines) - 1) * 4
    y = (H - total_h) // 2
    for i, line in enumerate(lines):
        x = (W - line_widths[i]) // 2
        draw.text((x, y), line, fill=color, font=font)
        y += line_heights[i] + 4
    
    # Crop to content
    bbox = img.getbbox()
    if bbox:
        padding = 30
        bbox = (max(0, bbox[0] - padding), max(0, bbox[1] - padding), 
                min(W, bbox[2] + padding), min(H, bbox[3] + padding))
        img = img.crop(bbox)
    
    img.save(f"{output_dir}/{name}.png")
    return img.size

# Example usage:
make_text_image("title", "Hello World", 56, "#ffd700")
make_text_image("subtitle", "A subtitle line", 22, "#4ecdc4")
```

### Step 2: Replace text `<div>` elements with `<img>` tags

In your HyperFrames composition HTML, replace each text element:

```html
<!-- BEFORE (doesn't work) -->
<div id="title" class="clip serif" data-start="0.5" data-duration="6" data-track-index="1"
     style="font-size:56px;color:#ffd700;">
  Hello World
</div>

<!-- AFTER (works) -->
<img id="title" src="text_images/title.png" class="img" data-start="0.5" data-duration="6" data-track-index="1" />
```

### Step 3: Keep `data-start` and `data-duration` attributes

HyperFrames' native clip system works on `<img>` tags. The `data-start`/`data-duration`/`data-track-index` attributes control visibility during playback. No GSAP animation needed for clip show/hide.

### Step 4: CRITICAL — Image paths must be relative to the project directory

**This is the #1 cause of "empty video" bugs.** The `text_images/` folder must exist **inside** the HyperFrames project directory, not at the workspace root. Relative paths like `src="text_images/title.png"` resolve relative to the HTML file's location.

```
✅ CORRECT:
project/
├── index.html
└── text_images/
    ├── title.png
    └── subtitle.png

❌ WRONG:
project/
└── index.html
workspace/
└── text_images/    ← images here won't be found!
    └── title.png
```

If images are generated at the workspace root, copy them into the project:
```bash
cp -r /workspace/text_images /workspace/garden-of-automation/garden-of-automation/text_images
```

### Step 5: Clip timing options

**Option A (simplest):** Let HyperFrames handle clip timing natively via `data-start`/`data-duration` on `<img>` tags. No GSAP needed for clip show/hide.

**Option B (smooth fades):** Use GSAP `autoAlpha` on `<img>` tags for fade-in/fade-out. This DOES work on images (unlike text divs). Set initial `opacity:0` inline on each img, then:
```javascript
var clips = [
  ['title', 0.5, 6],   // [id, start, duration]
  ['subtitle', 7, 6],
];
clips.forEach(function(c) {
  var id = c[0], start = c[1], dur = c[2];
  tl.to('#' + id, { autoAlpha: 1, duration: 0.5, ease: 'power2.out' }, start);
  tl.to('#' + id, { autoAlpha: 0, duration: 0.3, ease: 'power2.in' }, start + dur);
});
```

GSAP `autoAlpha` works on `<img>` tags but NOT on text `<div>` tags.

### Font Requirements
Text images require a proper TTF font. See **`references/font-discovery.md`** for font discovery across environments, including the KaTeX font fallback from Streamlit.

## Verification

After rendering, ALWAYS verify text appears in output:
```bash
ffmpeg -i output.mp4 -ss 00:00:03 -vframes 1 test.png
```
Then visually inspect `test.png` for text content. If text is missing, check:
1. `text_images/` directory exists inside project folder
2. Image filenames match `src` attributes exactly
3. `data-start` times are correct

## When HyperFrames Fails Completely: Pure PIL + FFmpeg Fallback

If HyperFrames continues to produce empty/black video, or if the text rendering workaround is too cumbersome, use a **pure Python/PIL + FFmpeg pipeline** instead. This approach:
- Generates frames directly with PIL (no browser, no JavaScript)
- Renders text, shapes, particles, gradients natively
- Encodes with FFmpeg
- Is fully deterministic with seeded RNG

### Font Discovery (CRITICAL)

**Standard TTF fonts may not be installed.** Always check before rendering:

```python
from PIL import ImageFont
import os

def find_font(size):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    # Fallback: KaTeX fonts from Streamlit package
    katex = "/home/hermeswebui/.hermes/home/.local/lib/python3.12/site-packages/streamlit/static/static/media/KaTeX_Main-Regular.ypZvNtVU.ttf"
    if os.path.exists(katex):
        return ImageFont.truetype(katex, size)
    return ImageFont.load_default()  # WARNING: tiny/unreadable
```

**If no fonts found:** PIL's default font is ~8px equivalent — unreadable at 1920×1080. You MUST find or download a proper font.

### Vignette (Fast Method)

Do NOT draw vignette pixel-by-pixel (too slow). Pre-compute as a mask:

```python
def make_vignette(w, h):
    v = Image.new('L', (w, h), 0)
    vd = ImageDraw.Draw(v)
    for r in range(max(w,h)//2, 0, -2):
        alpha = min(255, max(0, int(180 * max(0, 1 - r / (max(w,h)*0.4)))))
        vd.ellipse([w//2-r, h//2-r, w//2+r, h//2+r], fill=alpha)
    return v

# Apply per frame:
img.paste((0,0,0), mask=vignette)  # instant
```

### Performance Tips

- Pre-compute static overlays (vignette, cage bars) as images, paste per frame
- Use `ImageDraw` with `'RGBA'` mode for transparent overlays
- Save frames as PNG, encode with `ffmpeg -framerate 30 -i frame_%05d.png -c:v libx264 -crf 18`
- Expected speed: ~2-3 seconds per frame at 1920×1080 with text + nodes + particles
- Total render: ~2 hours for 2850 frames (95s × 30fps)
