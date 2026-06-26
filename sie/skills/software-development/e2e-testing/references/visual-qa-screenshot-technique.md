# Visual QA Screenshot Reference Notes (2026-05-23)

## Reference Image Download

URL: `https://ii.clsty.link/screenshots/ii-qs.1.jpg`

Direct `curl` works (with User-Agent), `urllib.request.urlretrieve` returns 403:
```bash
# Works
curl -sL -A "Mozilla/5.0" "https://ii.clsty.link/screenshots/ii-qs.1.jpg" -o /tmp/hwc-qa/references/ii-qs-1.jpg

# 403 Forbidden — requires browser UA
python3 -c "import urllib.request; urllib.request.urlretrieve(url, dest)"
```

Save location on host: `/tmp/hwc-qa/references/` — directory must exist before download.

## Screenshot Analysis with PIL (Python on Host)

The host (EndeavourOS) has Python 3.13 at `/usr/bin/python3` with Pillow at `/usr/lib/python3.13/site-packages/PIL/`.

**Python interpreter quirk:** The container maps `python3` to Python 3.12 under `/home/hermeswebui/.hermes/home/.local/lib/python3.12/site-packages/`, while the host has Python 3.13 at `/usr/lib/python3.13/site-packages/PIL/`. When running Python scripts via SSH, always use the full path `/usr/bin/python3` to use the host's interpreter.

**Wrong (uses container Python):**
```bash
ssh host "python3 script.py"  # container Python 3.12 — PIL path may differ
```

**Correct (uses host Python):**
```bash
ssh host "/usr/bin/python3 script.py"  # host Python 3.13
```

## Color Sampling Pattern

Use PIL to sample pixel colors at specific coordinates from a screenshot:
```python
from PIL import Image
img = Image.open('/tmp/hwc-qa/screenshots/screenshot.png')
r, g, b = img.convert('RGB').getpixel((x, y))
print(f'#{r:02x}{g:02x}{b:02x}')
```

## Content Bounds Detection

HWC renders as a centered column (e.g., 780px wide on 1440x900 viewport). Find the dark content bounds:
```python
min_x, min_y, max_x, max_y = w, h, 0, 0
for y in range(h):
    for x in range(w):
        r, g, b = img.getpixel((x, y))
        brightness = r*0.299 + g*0.587 + b*0.114
        if brightness < 200:  # non-white pixel
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)
crop = img.crop((min_x, min_y, max_x+1, max_y+1))
```

## Similarity Score (PIL only)

Resize both images to the same dimensions, then compute average channel difference:
```python
from PIL import Image

def similarity(img1_path, img2_path):
    img1 = Image.open(img1_path).convert('RGB')
    img2 = Image.open(img2_path).convert('RGB')
    # Resize to common dimensions
    tw, th = min(img1.width, img2.width), min(img1.height, img2.height)
    img1 = img1.resize((tw, th), Image.LANCZOS)
    img2 = img2.resize((tw, th), Image.LANCZOS)
    # Compute average pixel diff
    total = tw * th * 3
    diff_sum = sum(abs(a-b) for y in range(th) for x in range(tw)
                        for a, b in zip(img1.getpixel((x,y)), img2.getpixel((x,y))))
    avg_diff = diff_sum / total
    return (1 - avg_diff/255) * 100  # percent
```

## Two-Stage Comparison

1. **Regression check:** current screenshot vs baseline — detect accidental breakage
   - Threshold: <1% pixel diff = PASS
   - If FAIL: something broke in the last commit

2. **Reference check:** current screenshot vs design reference — score against target
   - Threshold: ≥85% similarity = PASS
   - If FAIL: CSS/tokens don't match the design spec

## Illogical Impulse Reference Colors (from pixel analysis)

Target design at 1440×900 (reference image `ii-qs-1.jpg`):
- Top bar: `#1c1c1d` (near-black)
- Left panel: `#23231f` / `#1d1d1c` (very dark gray with slight green)
- Center area: `#242424` (dark gray)
- Bottom dock: `#313030` (medium dark gray)

HWC before fix: top bar was `#bababd` (3× too bright), indicating `bg-white/5` or similar light utility class was being used instead of the dark design token.