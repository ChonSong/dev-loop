"""
Animated Explainer Video Generator — PIL + FFmpeg Pipeline
============================================================
Produces H.264 MP4 videos from Python-rendered frames.
No manim dependency. Works in Docker/sandboxed environments.

Usage:
  1. Define scene functions: def scene_name(img, draw, t): ...
  2. In main(), create SceneEncoder and call write_frames() / write_static()
  3. Run: python3 generate.py

Each scene function receives:
  - img:  PIL Image (RGB, 1280x720)
  - draw: ImageDraw.Draw
  - t:    float, 0.0 → 1.0 over the scene duration
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import subprocess, os, math, urllib.request

# ─── CONFIG ───────────────────────────────────────────────────────────────────
W, H = 1280, 720
FPS = 30
OUTPUT = "final.mp4"
FFMPEG = "ffmpeg"  # or "/workspace/bin/ffmpeg" for static build

BG = (10, 10, 10)
PRIMARY = (0, 245, 255)
SECONDARY = (255, 0, 255)
ACCENT = (57, 255, 20)
TEXT_COLOR = (234, 234, 234)
DIM_COLOR = (85, 85, 85)
WARN = (255, 68, 68)

# ─── FONTS ────────────────────────────────────────────────────────────────────
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
os.makedirs(FONT_DIR, exist_ok=True)

def ensure_font(name, url):
    path = os.path.join(FONT_DIR, name)
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
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

# ─── HELPERS ──────────────────────────────────────────────────────────────────

def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

def draw_center(draw, y, text, font, color):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    x = (W - tw) // 2
    draw.text((x, y), text, font=font, fill=color)

def draw_rounded_rect(draw, xy, radius=12, fill=None, outline=None, width=2):
    x0, y0, x1, y1 = xy
    if fill:
        draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill)
    if outline:
        draw.rounded_rectangle([x0, y0, x1, y1], radius=radius,
                                outline=outline, width=width)

# ─── ENCODER ──────────────────────────────────────────────────────────────────

class SceneEncoder:
    def __init__(self, output=OUTPUT, w=W, h=H, fps=FPS, ffmpeg_path=FFMPEG):
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
        img = Image.new("RGB", (self.w, self.h), BG)
        draw = ImageDraw.Draw(img)
        render_fn(img, draw, 1.0, **kwargs)
        for _ in range(int(duration_sec * self.fps)):
            self.write_frame(img)

    def write_frames(self, duration_sec, render_fn, **kwargs):
        n = int(duration_sec * self.fps)
        for i in range(n):
            t = i / max(n - 1, 1)
            img = Image.new("RGB", (self.w, self.h), BG)
            draw = ImageDraw.Draw(img)
            render_fn(img, draw, t, **kwargs)
            self.write_frame(img)

    def close(self):
        self.proc.stdin.close()
        self.proc.wait()
        size_mb = os.path.getsize(OUTPUT) / (1024 * 1024)
        print(f"Done! {size_mb:.1f} MB → {OUTPUT}")

# ─── SCENE TEMPLATE ───────────────────────────────────────────────────────────
# Copy and modify this template for each scene:

def scene_example(img, draw, t):
    """Example scene — replace with your content."""
    ft = load_font(36, bold=True)
    fs = load_font(22)

    # Fade in over first 40%
    a = min(1.0, t * 2.5) if t < 0.4 else 1.0
    color = lerp_color(BG, PRIMARY, a)

    draw_center(draw, 300, "Your Title Here", ft, color)
    draw_center(draw, 360, "Subtitle here", fs, SECONDARY)

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    enc = SceneEncoder()

    # Add your scenes here:
    # enc.write_static(2.0, scene_example)
    # enc.write_frames(5.0, scene_example)

    enc.close()

if __name__ == "__main__":
    main()
