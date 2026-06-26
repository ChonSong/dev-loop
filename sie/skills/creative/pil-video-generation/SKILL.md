---
name: pil-video-generation
description: Generate MP4 videos using Python PIL/Pillow for frame rendering + FFmpeg for encoding. Use when browser-based video tools (HyperFrames, etc.) fail or when you need full control over frame-by-frame rendering. Supports text, shapes, particles, gradients, vignettes, and animated transitions.
---

# PIL Video Generation Pipeline

Generate MP4 videos by rendering frames with Python/PIL and encoding with FFmpeg. No browser, no JavaScript required.

## When to Use

- Browser-based video tools fail or produce empty output
- You need pixel-perfect control over every frame
- Text rendering must be reliable (no GSAP/browser bugs)
- You need deterministic output with seeded RNG
- HyperFrames or similar tools are unavailable/broken

## Pipeline

```
WRITE SCRIPT --> GENERATE FRAMES --> ENCODE MP4 --> UPLOAD
```

## Prerequisites

- Python 3.10+, PIL/Pillow (`pip install pillow`), ffmpeg

### Font Discovery (CRITICAL)

Standard TTF fonts may not be installed. **Always check:**

```python
from PIL import ImageFont
import os

def get_font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                pass
    # Fallback: KaTeX fonts from Streamlit package (always present)
    katex_dir = "/home/hermeswebui/.hermes/home/.local/lib/python3.12/site-packages/streamlit/static/static/media/"
    katex_font = os.path.join(katex_dir, "KaTeX_SansSerif-Bold.CFMepnvq.ttf" if bold else "KaTeX_Main-Regular.ypZvNtVU.ttf")
    if os.path.exists(katex_font):
        return ImageFont.truetype(katex_font, size)
    return ImageFont.load_default()  # WARNING: ~8px equivalent, unreadable
```

**If no fonts found:** PIL's default font is ~8px — unreadable at 1920×1080. You MUST find or use KaTeX fonts.

## Frame Generation Script Template

```python
import os, math, random, subprocess
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
FPS = 30
DURATION = 95
TOTAL_FRAMES = FPS * DURATION
OUT_DIR = "frames"
OUTPUT = "output.mp4"

rng = random.Random(42)  # Seeded for determinism

def get_font(size):
    # ... (font discovery from above)

def draw_vignette(img):
    """Apply radial vignette (fast method using pre-computed mask)."""
    v = Image.new('L', (W, H), 0)
    vd = ImageDraw.Draw(v)
    for r in range(max(W,H)//2, 0, -2):
        alpha = min(255, max(0, int(180 * max(0, 1 - r / (max(W,H)*0.4)))))
        vd.ellipse([W//2-r, H//2-r, W//2+r, H//2+r], fill=alpha)
    img.paste((0,0,0), mask=v)

def draw_text(draw, text, x, y, font, fill):
    """Draw multiline text centered at x, y."""
    lines = text.split('\n')
    bb = draw.textbbox((0,0),"Ay",font=font)
    lh = int((bb[3]-bb[1])*1.3)
    total = lh*len(lines)
    cy = y - total//2
    for line in lines:
        bb = draw.textbbox((0,0),line,font=font)
        lw = bb[2]-bb[0]
        draw.text((x-lw//2, cy), line, fill=fill, font=font)
        cy += lh

def text_opacity(t, start, end, fi=0.5, fo=0.3):
    """Smooth fade in/out for text visibility."""
    if t < start or t > end: return 0
    if t < start+fi: return (t-start)/fi  # linear fade in
    if t > end-fo: return (end-t)/fo      # linear fade out
    return 1.0

def ease(t): return t*t*(3-2*t)  # smoothstep

# --- Main loop ---
os.makedirs(OUT_DIR, exist_ok=True)
for frame in range(TOTAL_FRAMES):
    t = frame / FPS
    img = Image.new('RGB', (W, H), bg_color)
    draw = ImageDraw.Draw(img, 'RGBA')
    
    # Draw your elements here...
    # - Background, vignette, particles, nodes, text, etc.
    
    img.save(f"{OUT_DIR}/frame_{frame:05d}.png")
    if frame % 100 == 0:
        print(f"  {frame}/{TOTAL_FRAMES} ({100*frame/TOTAL_FRAMES:.0f}%)")

# --- Encode ---
subprocess.run([
    'ffmpeg', '-y', '-framerate', str(FPS),
    '-i', f'{OUT_DIR}/frame_%05d.png',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
    '-pix_fmt', 'yuv420p', '-movflags', '+faststart', OUTPUT
])
```

## Vignette (Fast Method)

**Do NOT draw pixel-by-pixel** — too slow. Pre-compute as L-channel mask:

```python
vignette = Image.new('L', (W, H), 0)
vd = ImageDraw.Draw(vignette)
for r in range(max(W,H)//2, 0, -2):
    alpha = min(255, max(0, int(180 * max(0, 1 - r / (max(W,H)*0.4)))))
    vd.ellipse([W//2-r, H//2-r, W//2+r, H//2+r], fill=alpha)

# Per frame (instant):
img.paste((0,0,0), mask=vignette)
```

## Performance

- ~2-3 sec/frame at 1920×1080 with text + nodes + particles + vignette
- 2850 frames ≈ ~2 hours render time
- FFmpeg encoding: ~30 seconds

## Verification

Always verify output:
```bash
ffmpeg -i output.mp4 -ss 00:00:10 -vframes 1 test.png
```
Check `test.png` for text readability, correct colors, and animation.

---

## McKinsey-Style Chart Drawing Patterns

When the user wants data-driven, professional video segments (not just poetic visuals), use these chart drawing functions. See `presentation-design` skill for slide principles and `references/chart-layouts.md` for visual templates.

### Horizontal Bar Chart

```python
def draw_hbar_chart(draw, categories, values, colors, chart_x0=200, chart_y0=150, bar_h=55, bar_max_w=1200):
    \"\"\"Draw horizontal bar chart with labels and values.\"\"\"
    f_label = get_font(20)
    f_val = get_font(22, bold=True)
    for i, (name, val, color) in enumerate(zip(categories, values, colors)):
        y = chart_y0 + i * (bar_h + 12)
        w = int(bar_max_w * val / max(values))
        draw.rectangle([chart_x0, y, chart_x0 + w, y + bar_h], fill=color)
        draw.text((chart_x0 - 10, y + bar_h//2), name, fill=TEXT, font=f_label, anchor="rm")
        draw.text((chart_x0 + w + 10, y + bar_h//2), str(val), fill=color, font=f_val, anchor="lm")
```

### Two-Column Comparison

```python
def draw_comparison(draw, col1_x, col2_x, label1, val1, label2, val2, bar_h=500, bar_w=120):
    \"\"\"Side-by-side comparison bars.\"\"\"
    f_label = get_font(24)
    f_num = get_font(48, bold=True)
    h1 = int(bar_h * val1 / 100)
    h2 = int(bar_h * val2 / 100)
    draw.rectangle([col1_x - bar_w//2, bar_bottom - h1, col1_x + bar_w//2, bar_bottom], fill=color1)
    draw.rectangle([col2_x - bar_w//2, bar_bottom - h2, col2_x + bar_w//2, bar_bottom], fill=color2)
    draw.text((col1_x, bar_bottom - h1 - 20), f\"{val1}%\", fill=color1, font=f_num, anchor=\"mm\")
    draw.text((col2_x, bar_bottom - h2 - 20), f\"{val2}%\", fill=color2, font=f_num, anchor=\"mm\")
```

### Hero Number Slide

```python
def draw_hero_number(draw, number_str, label, comparison_text, callout, num_color=GOLD):
    \"\"\"Single large number dominating frame.\"\"\"
    f_num = get_font(120, bold=True)
    f_body = get_font(26)
    f_label = get_font(22)
    f_callout = get_font(22, bold=True)
    draw.text((960, 420), number_str, fill=num_color, font=f_num, anchor="mm")
    draw.text((960, 520), label, fill=TEXT, font=f_body, anchor="mm")
    draw.text((960, 630), comparison_text, fill=MUTED, font=f_label, anchor="mm")
    draw.text((960, 880), callout, fill=num_color, font=f_callout, anchor="mm")
```

### Icon Array

```python
def draw_icon_array(draw, count, filled, icon_y, icon_r=25, color=GOLD, empty_color=GREY):
    \"\"\"Row of person icons showing proportions.\"\"\"
    total_w = count * 60
    start_x = 960 - total_w // 2 + 30
    for i in range(count):
        x = start_x + i * 60
        fill = color if i < filled else empty_color
        draw.ellipse([x - icon_r, icon_y - icon_r, x + icon_r, icon_y + icon_r], fill=fill)
```

### Arrow Helper

```python
def draw_arrow(d, x1, y1, x2, y2, fill, width=3):
    \"\"\"Draw an arrow between two points with arrowhead.\"\"\"
    d.line([(x1,y1),(x2,y2)], fill=fill, width=width)
    dx, dy = x2-x1, y2-y1
    length = math.sqrt(dx*dx + dy*dy)
    if length > 1:
        ux, uy = dx/length, dy/length
        d.polygon([
            (x2, y2),
            (x2 - ux*12 - uy*12*0.3, y2 - uy*12 + ux*12*0.3),
            (x2 - ux*12 + uy*12*0.3, y2 - uy*12 - ux*12*0.3)
        ], fill=fill)
```

---

## Adding Audio: TTS Narration + Background Music

### Step 1: Generate TTS Narration for Each Segment

Use the `text_to_speech` tool to generate voiceover for each segment. Write concise narration scripts (~2-3 seconds per sentence):

```python
# Generate per segment via text_to_speech tool:
# text_to_speech(text="Your narration here", output_path="audio/01_segment.mp3")
```

### Step 2: Mux Audio with FFmpeg (adelay + amix)

Place each TTS clip at its segment's start time using FFmpeg's `adelay` filter, then mix all streams together:

```bash
FFMPEG=/workspace/bin/ffmpeg
VIDEO=output.mp4
OUTPUT=output-with-audio.mp4

# Segment start times in milliseconds
SEG_STARTS_MS=(0 5000 14000 24000 ...)

INPUTS=""
FILTER=""
STREAMS=""

for i in $(seq 0 9); do
    stream=$((i + 1))
    padded=$(printf "%02d" $((i + 1)))
    start_ms=${SEG_STARTS_MS[$i]}
    f=$(ls audio/${padded}_*.mp3 2>/dev/null)
    [ -z "$f" ] && continue
    
    INPUTS="$INPUTS -i $f"
    FILTER="${FILTER}[${stream}:a]adelay=${start_ms}|${start_ms},apad=whole_dur=83000[a${stream}];"
    STREAMS="${STREAMS}[a${stream}]"
done

FILTER="${FILTER}${STREAMS}amix=inputs=10:duration=first:dropout_transition=0,volume=1.5[aout]"

$FFMPEG -y -i $VIDEO $INPUTS \
  -filter_complex "$FILTER" \
  -map 0:v -map "[aout]" \
  -c:v copy -c:a aac -b:a 192k \
  -shortest $OUTPUT
```

**Key FFmpeg notes:**
- `adelay` takes milliseconds, one per audio channel (repeat for stereo: `5000|5000`)
- `apad=whole_dur=83000` pads each clip to the full video duration
- `amix` blends all streams; adjust `volume=1.5` if individual clips are quiet
- `-c:v copy` is fast (no re-encode of video)

### Step 3: Suno AI Background Music

Generate a custom background track using Suno AI. See `creative/songwriting-and-ai-music` for full Suno prompting guide.

**Example style prompt:**
```
Cinematic ambient electronic, 2020s tech documentary style, atmospheric synth pads with a slow evolving harmonic progression, minimal percussion, deep sub-bass pulses, 80 BPM, D minor key, ethereal female humming vocal sample, gradual dynamic build from sparse to lush, Berlin-school influences, analog warmth with modern clarity, wide stereo field, reverb-drenched textures, introspective and awe-inspiring mood, suitable as a documentary underscore.
```

**Dynamic arc description:**
```
Begins as a sparse, solitary piano note over a deep sub-bass drone. Slowly introduces layered synth pads that evolve through the piece. At 30 seconds, a subtle pulsing rhythm enters — like a heartbeat. The piece builds in density and warmth without ever reaching a dramatic climax. Fades out gently in the final 10 seconds.
```

**To add Suno music to the video:**
1. Generate the track with Suno Custom Mode using the prompt above
2. Download the MP3 to `audio/background.mp3`
3. Add it as an 11th input in the FFmpeg command above, mixed at lower volume
4. Use `volume=0.3` for the background track vs `volume=1.5` for TTS

---

## Related Skills

- `presentation-design` — McKinsey slide principles, chart layout templates, color palettes
- `hyperframes-text-workaround` — font discovery, PIL frame generation basics
- `songwriting-and-ai-music` — Suno AI music prompt engineering
- `kanban-video-orchestrator` — multi-agent video production pipeline (for complex projects)

