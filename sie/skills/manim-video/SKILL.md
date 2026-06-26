---
name: manim-video
description: "Manim CE animations: 3Blue1Brown math/algo videos."
version: 1.1.0
platforms: [linux, macos, windows]
---

# Manim Video Production Pipeline

## When to use

Use when users request: animated explanations, math animations, concept visualizations, algorithm walkthroughs, technical explainers, 3Blue1Brown style videos, or any programmatic animation with geometric/mathematical content.

## Prerequisites

Run `scripts/setup.sh` to verify all dependencies. Requires: Python 3.10+, Manim Community Edition v0.20+ (`pip install manim`), LaTeX (`texlive-full` on Linux, `mactex` on macOS), and ffmpeg. Reference docs tested against Manim CE v0.20.1.

## ⚠️ Environment-Specific Blockers (DO NOT SKIP THIS SECTION)

Before attempting to use Manim, verify the environment can support it. On containerized or restricted environments:

### libcairo Dependency (BLOCKER)
Manim requires `pycairo` which needs the system-level `libcairo` shared library. **This cannot be installed without root/sudo access.**

**Symptoms of this blocker:**
- `pip install pycairo` fails with meson/build errors about missing C compiler or cairo headers
- `import cairocffi` raises `OSError: no library called "cairo-2" was found`
- `apt-get install libcairo2-dev` fails with permission denied

**Workaround:** Use the **Python/PIL + FFmpeg fallback** (see `creative/video-generation-fallback`) instead of Manim when libcairo is unavailable. This approach:
- Uses PIL/Pillow for frame generation (text, shapes, particles, gradients)
- Uses FFmpeg for H.264 encoding
- Supports all the same visual elements: text, nodes, edges, particles, vignettes, transitions
- Is fully deterministic with seeded RNG
- Does NOT require any system libraries beyond ffmpeg

### Font Availability
Standard TTF fonts (DejaVu, Liberation, etc.) may not be installed. PIL falls back to a minimal default font that is **unreadably small** at video resolutions.

**Check before rendering:**
```python
from PIL import ImageFont
import os
for path in ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
             "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"]:
    if os.path.exists(path):
        font = ImageFont.truetype(path, 48)
        break
```

**If no fonts found:** Use KaTeX fonts bundled with Streamlit:
```python
FONT = "/home/hermeswebui/.hermes/home/.local/lib/python3.12/site-packages/streamlit/static/static/media/KaTeX_Main-Regular.ypZvNtVU.ttf"
```
These are proper TTF files (50KB+) that render at correct sizes.

**⚠️ pycairo blocker on restricted environments:** `pip install manim` pulls in `pycairo`, which requires system-level cairo dev headers (`libcairo2-dev` on Debian/Ubuntu, `cairo-devel` on Fedora/RHEL). On containers or shared hosts without root/sudo, `pip install pycairo` fails with a meson build error. **Manim is unusable without root.** Before attempting installation, check with `python3 -c "import manim"` — if it fails on pycairo, use the Python + PIL + FFmpeg fallback pipeline instead (see `creative/hyperframes` skill's `references/pil-fallback.md`).
