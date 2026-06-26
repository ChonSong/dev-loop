# PIL + FFmpeg Fallback Pipeline

## When to use this

Use when manim's C dependencies (pycairo, pango) can't be installed — Docker sandboxes, minimal containers, systems without apt/root. This pipeline produces clean explainer videos with smooth transitions using only PIL + NumPy + ffmpeg.

## Prerequisites check

```bash
# These three must be available:
python3 -c "from PIL import Image; import numpy; print('ok')"
which ffmpeg || echo "MISSING: download static build from johnvansickle.com/ffmpeg"
find /usr/share/fonts /usr/local/share/fonts -name "*.ttf" 2>/dev/null | head -3
```

If no fonts found, see Font Setup section below.

## Architecture

```
Scene functions (PIL ImageDraw) → NumPy raw RGB → ffmpeg stdin → H.264 MP4
```

One Python script per project. Each scene is a `render_fn(img, draw, t)` where `t` goes from 0→1 over the scene duration.

## SceneEncoder class (reusable)

```python
import subprocess, os, numpy as np
from PIL import Image

class SceneEncoder:
    def __init__(self, output, w=1280, h=720, fps=30, ffmpeg_path="ffmpeg"):
        self.w, self.h, self.fps = w, h, fps
        cmd = [
            ffmpeg_path, "-y",
            "-f", "rawvideo", "-vcodec", "rawvideo",
            "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(fps),
            "-i", "-",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-preset", "medium", "-crf", "18",
            "-movflags", "+faststart",
            output
        ]
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                      stderr=subprocess.DEVNULL)

    def write_frame(self, img):
        self.proc.stdin.write(np.array(img).tobytes())

    def write_static(self, duration_sec, render_fn, **kwargs):
        img = Image.new("RGB", (self.w, self.h), (10, 10, 10))
        draw = ImageDraw.Draw(img)
        render_fn(img, draw, 1.0, **kwargs)
        for _ in range(int(duration_sec * self.fps)):
            self.write_frame(img)

    def write_frames(self, duration_sec, render_fn, **kwargs):
        n = int(duration_sec * self.fps)
        for i in range(n):
            t = i / max(n - 1, 1)
            img = Image.new("RGB", (self.w, self.h), (10, 10, 10))
            draw = ImageDraw.Draw(img)
            render_fn(img, draw, t, **kwargs)
            self.write_frame(img)

    def close(self):
        self.proc.stdin.close()
        self.proc.wait()
```

## Color palette: Neon Tech (recommended for technical content)

```python
BG      = (10, 10, 10)     # near-black
PRIMARY = (0, 245, 255)     # cyan — titles, key concepts
SECONDARY = (255, 0, 255)   # magenta — subtitles, supporting
ACCENT  = (57, 255, 20)     # green — highlights, success
TEXT    = (234, 234, 234)   # off-white — body text
DIM     = (85, 85, 85)      # structural elements
WARN    = (255, 68, 68)     # red — errors
```

## Smooth color interpolation

```python
def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
```

Use this for progressive reveal: `color = lerp_color(BG, PRIMARY, alpha)` where `alpha` ramps from 0→1 over the first 30% of a scene.

## Font Setup (critical)

**Pillow falls back to an illegible bitmap font if no `.ttf` is found.** Always verify fonts exist, then download if needed:

```python
import urllib.request, os

FONT_DIR = "/workspace/fonts"
os.makedirs(FONT_DIR, exist_ok=True)

def ensure_font(name, url):
    path = f"{FONT_DIR}/{name}"
    if not os.path.exists(path):
        print(f"Downloading {name}...")
        urllib.request.urlretrieve(url, path)
    return path

FONT_REGULAR = ensure_font("JetBrainsMono-Regular.ttf",
    "https://github.com/JetBrains/JetBrainsMono/raw/master/fonts/ttf/JetBrainsMono-Regular.ttf")
FONT_BOLD = ensure_font("JetBrainsMono-Bold.ttf",
    "https://github.com/JetBrains/JetBrainsMono/raw/master/fonts/ttf/JetBrainsMono-Bold.ttf")

def load_font(size, bold=False):
    path = FONT_BOLD if bold else FONT_REGULAR
    return ImageFont.truetype(path, size)
```

JetBrains Mono is recommended — its legibility at 16px+ in video is excellent.

## Centered text helper

```python
def draw_center(draw, y, text, font, color):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    x = (1280 - tw) // 2
    draw.text((x, y), text, font=font, fill=color)
```

## Rounded rectangle (for boxes/cards)

```python
def draw_rounded_rect(draw, xy, radius=12, fill=None, outline=None, width=2):
    x0, y0, x1, y1 = xy
    if fill:
        draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill)
    if outline:
        draw.rounded_rectangle([x0, y0, x1, y1], radius=radius,
                                outline=outline, width=width)
```

## Animation timing conventions (30fps video)

| Element | Frames | Duration |
|---------|--------|----------|
| Title write-in | 45 | 1.5s |
| Subtitle fade | 30 | 1.0s |
| Box appear | 15 | 0.5s |
| Arrow draw | 10 | 0.3s |
| Static hold | 45-90 | 1.5-3.0s |
| Full scene | 90-210 | 3-7s |

Use `t` (0→1) parameter: compute `alpha = min(1.0, t * 3)` for a fast fade-in over first 33%.

## Scene structure pattern

Each scene function takes `(img, draw, t, **kwargs)`:

```python
def scene_title(img, draw, t):
    ft = load_font(44, bold=True)
    fs = load_font(28)

    # Phase-based alpha
    a = min(1.0, t * 3) if t < 0.4 else max(0, 1.0 - (t - 0.7) * 3)
    color = lerp_color(BG, PRIMARY, a)

    draw_center(draw, 260, "Title Text", ft, color)
```

## ffmpeg static binary (no install needed)

If `ffmpeg` is not in PATH:

```bash
# Download static build (works on any Linux x86_64):
curl -sL "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz" \
  -o /tmp/ffmpeg.tar.xz
tar xf /tmp/ffmpeg.tar.xz -C /tmp/
mkdir -p /workspace/bin
cp /tmp/ffmpeg-*-static/ffmpeg /workspace/bin/
# Use: FFMPEG = "/workspace/bin/ffmpeg"
```

## Project structure

```
project-name/
  plan.md              # narrative arc, scene list, timing
  generate.py          # all scene renderers + SceneEncoder
  fonts/               # downloaded .ttf files
  final.mp4            # output
  checks/              # debug frame stills
```

## Pros vs manim

| Aspect | PIL + FFmpeg | Manim |
|--------|-------------|-------|
| Dependencies | PIL, NumPy, ffmpeg binary | C libs, LaTeX, Python pkg |
| Installable in Docker | ✅ Yes | ❌ Needs apt + gcc |
| Math equations | ❌ PIL only (bitmap) | ✅ LaTeX MathTex |
| 3D | ❌ 2D only | ✅ ThreeDScene |
| Animation richness | Basic (fades, color lerp) | Full (transforms, updaters) |
| Render speed | ~100ms/frame | 30-120s/frame |
| Explainer diagrams | ✅ Excellent | ✅ Excellent |
