# PIL Fallback Rendering for HyperFrames

When `hyperframes render` fails because the environment lacks X11/GTK shared libraries (common in Docker containers and CI runners), use this pure-Python fallback approach.

## When to Use This Fallback

- `hyperframes render` fails with `libglib-2.0.so.0: cannot open shared object file`
- `npx puppeteer` or Playwright fails with missing shared libraries
- No root access to install system packages
- `hyperframes doctor` reports Chrome binary found but render hangs or crashes

## Approach

Use Pillow (PIL) to draw each frame programmatically, then encode to video with ffmpeg.

### Prerequisites

```bash
pip install Pillow imageio[ffmpeg] numpy
```

`imageio[ffmpeg]` bundles a static ffmpeg binary — no system install needed.

### Key Constraints

| Constraint | Impact | Mitigation |
|---|---|---|
| No system TTF fonts | PIL default bitmap font only (small, pixelated) | **Download TTF fonts at runtime** from GitHub (see below) and load with `ImageFont.truetype()`. Inter + JetBrains Mono work well. |
| No GSAP animations | Must implement easing math manually | Use simple ease functions (cubic, expo, back) — see below |
| ~5 fps render rate at 1920×1080 | Slow for long videos | Reduce to 15fps output; pre-render static background as NumPy array |
| No browser compositing | No CSS transitions, filters, or complex layout | Keep scenes simple: text + cards + tables |

### Easing Functions

```python
def ease_out_cubic(t): t=max(0,min(1,t)); return 1-(1-t)**3
def ease_out_expo(t): t=max(0,min(1,t)); return 1-pow(2,-10*t) if t<1 else 1
def ease_out_back(t): t=max(0,min(1,t)); c=1.70158; return 1+(c+1)*pow(t-1,3)+c*pow(t-1,2)
def ease_in_quad(t): t=max(0,min(1,t)); return t*t

def anim(ts, start, dur, ease=ease_out_cubic):
    return 0 if ts<start else ease(min(1,(ts-start)/dur))
```

### Rendering Pattern

```python
import numpy as np
from PIL import Image, ImageDraw

# 1. Pre-render static background ONCE as NumPy array
bg = np.full((HEIGHT, WIDTH, 3), BG_COLOR, dtype=np.uint8)
# Draw grid pattern on bg...

# 2. Per-frame: copy bg, draw scene elements
for frame_num in range(total_frames):
    t = frame_num / fps
    arr = bg.copy()
    img = Image.fromarray(arr)
    draw = ImageDraw.Draw(img)
    # Draw scene elements based on t using anim() for entrances
    img.save(f"frames/frame_{frame_num:06d}.png")
```

### Encoding (use ffmpeg directly — much faster than imageio)

```bash
ffmpeg -y -framerate 15 -i frames/frame_%06d.png \
  -c:v libx264 -preset ultrafast -crf 23 \
  -pix_fmt yuv420p -movflags +faststart silent.mp4
```

### Audio Mux

```bash
ffmpeg -y -i silent.mp4 \
  -f concat -safe 0 -i audio_list.txt \
  -map 0:v -map 1:a \
  -c:v copy -c:a aac -b:a 128k \
  -shortest output.mp4
```

### Encoding (use ffmpeg directly — much faster than imageio)

```bash
ffmpeg -y -framerate 15 -i frames/frame_%06d.png \
  -c:v libx264 -preset ultrafast -crf 23 \
  -pix_fmt yuv420p -movflags +faststart silent.mp4
```

### Audio Mux

```bash
ffmpeg -y -i silent.mp4 \
  -f concat -safe 0 -i audio_list.txt \
  -map 0:v -map 1:a \
  -c:v copy -c:a aac -b:a 128k \
  -shortest output.mp4
```

### Downloading TTF Fonts at Runtime

When no system fonts are available, download Inter and JetBrains Mono directly from GitHub:

```bash
mkdir -p /tmp/fonts && cd /tmp/fonts
curl -sL -o Inter-Bold.otf "https://raw.githubusercontent.com/rsms/inter/v3.19/docs/font-files/Inter-Bold.otf"
curl -sL -o Inter-Regular.otf "https://raw.githubusercontent.com/rsms/inter/v3.19/docs/font-files/Inter-Regular.otf"
curl -sL -o Inter-Medium.otf "https://raw.githubusercontent.com/rsms/inter/v3.19/docs/font-files/Inter-Medium.otf"
curl -sL -o Inter-SemiBold.otf "https://raw.githubusercontent.com/rsms/inter/v3.19/docs/font-files/Inter-SemiBold.otf"
curl -sL -o JetBrainsMono-Regular.ttf "https://raw.githubusercontent.com/JetBrains/JetBrainsMono/master/fonts/ttf/JetBrainsMono-Regular.ttf"
curl -sL -o JetBrainsMono-Bold.ttf "https://raw.githubusercontent.com/JetBrains/JetBrainsMono/master/fonts/ttf/JetBrainsMono-Bold.ttf"
```

Load in Python:
```python
from PIL import ImageFont
font = ImageFont.truetype("/tmp/fonts/Inter-Bold.otf", 72)
```

**Note:** Inter v4 paths return 404. Use `v3.19` tag. JetBrains Mono uses `master` branch.

### 1fps Keyframe + ffmpeg Frame Blending (Fastest Approach)

For long videos (~3min), rendering every frame at 15-24fps via PIL is slow (~5fps render rate = 15min+). Instead:

1. **Render at 1fps** — only N frames for N seconds of video (e.g., 196 frames for 196s)
2. **Use ffmpeg `tblend` filter** to smooth-blend between keyframes to target fps

```python
# Render loop: 1 frame per second
for fn in range(DURATION):
    t = fn / 1.0  # 1 fps
    img = render_frame(bg, t)
    img.save(f"frames/frame_{fn:06d}.png")
```

```bash
ffmpeg -y -framerate 1 -i frames/frame_%06d.png \
  -vf "tblend=all_mode=average,framestep=2,framerate=30" \
  -c:v libx264 -preset fast -crf 18 \
  -pix_fmt yuv420p -movflags +faststart -r 30 output.mp4
```

**Trade-off:** Works well for slideshow-style content (text, cards, tables). NOT suitable for fast motion or animation. The `tblend` filter creates smooth crossfade-like transitions between keyframes.

**Alternative:** Use `minterpolate` for motion-compensated interpolation (much slower encode but smoother output):
```bash
-vf "minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1"
```

### Performance Tips

- **Pre-render background**: Draw grid/glow once as NumPy array, `.copy()` per frame
- **Reduce grid density**: Every 120px instead of 60px (4x fewer draw calls)
- **15fps is acceptable**: For presentation slideshows, 15fps is smooth enough
- **Skip re-rendering**: Save frames to disk, encode separately  
- **Use ffmpeg directly**: 10-50x faster than imageio for PNG sequences
- **No system ffmpeg?**: `python3 -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"` finds the static bundled binary