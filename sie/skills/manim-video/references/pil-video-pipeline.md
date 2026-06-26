# PIL-Based Video Production Pipeline

## When to use

Use when you need to generate explainer/technical videos in environments where Manim can't be installed (containers, sandboxes, minimal Linux). Uses only Python + PIL + NumPy + ffmpeg — zero C dependencies.

## Setup

```bash
# 1. Download ffmpeg static binary (no package manager needed)
curl -sL https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz -o /tmp/ffmpeg.tar.xz
tar xf /tmp/ffmpeg.tar.xz -C /tmp
cp /tmp/ffmpeg-*-static/ffmpeg /workspace/bin/ffmpeg

# 2. Download fonts (containers usually have ZERO system fonts)
mkdir -p /workspace/fonts
curl -sL "https://github.com/JetBrains/JetBrainsMono/raw/master/fonts/ttf/JetBrainsMono-Regular.ttf" \
  -o /workspace/fonts/JetBrainsMono-Regular.ttf
curl -sL "https://github.com/JetBrains/JetBrainsMono/raw/master/fonts/ttf/JetBrainsMono-Bold.ttf" \
  -o /workspace/fonts/JetBrainsMono-Bold.ttf

# 3. Python deps (usually pre-installed)
pip install numpy scipy
```

## Architecture

Single Python script per project. Renders frames via PIL, pipes raw RGB to ffmpeg for H.264 encoding.

## Easing Functions

Always use easing — linear motion feels robotic.

- ease_in_out(t): t*t*(3-2*t) — default for most animations
- ease_out_cubic(t): 1-(1-t)^3 — fast start, gentle landing for reveals
- ease_out_back(t): slight overshoot for emphasis

## Transitions

- fade: Cross-fade between scenes (dramatic)
- wipe_left: Wipe from right to left (forward progress)
- wipe_down: Wipe from top to bottom (reveal)
- dissolve: Pixel dissolve (chaotic/creative)

All transitions should use ease_in_out for timing.

## Visual Design System

### Palette (Neon Tech)
BG=(10,10,10), PRIMARY=cyan, SECONDARY=magenta, ACCENT=green, TEXT=off-white

### Opacity Layering
Primary=1.0, Context=0.4, Structural=0.15

### Typography
Title 44-48pt bold, Heading 28-32pt bold, Body 18-22pt, Label 14-16pt. All monospace.

### Decorations
Glow circles, rounded boxes, arrows, dashed lines, progress bars, dot grid backgrounds, number badges.

## Scene Design Rules

1. One new idea per scene
2. Progressive reveal — elements appear sequentially
3. Staggered entry using t*N - i*stagger formula
4. Breathing room — hold_after 1-1.5s per scene
5. Smooth transitions between scenes (never hard-cut)
6. Color = meaning (consistent across scenes)
7. >15% empty space in every frame

## Font Handling in Containers

Most containers have NO system fonts. Always download TTFs to a known path and reference absolutely. Never rely on system font paths like /usr/share/fonts/.
