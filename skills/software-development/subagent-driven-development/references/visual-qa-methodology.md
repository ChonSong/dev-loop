# Visual QA Methodology Reference

## Why Pixel-Diff Fails

**Real example (2026-05-24, hermes-web-computer):**
- Pixel-diff reported: **81.9% similar** 
- Human perception: **~5% similar**
- Root cause: Comparing a tiling window manager (HWC) to a notes app (Nomie/Ilogical Impulse) — fundamentally different apps

**Why pixel-diff is the wrong metric:**
1. Glassmorphism + blur changes every underlying pixel even when perceived color is identical
2. Anti-aliasing / sub-pixel rendering adds noise → same text = different pixels
3. Whole-image aggregation hides component-level mismatches
4. Identical colors at wrong locations = high pixel match, low actual similarity

---

## The Correct Method: Perceptual Color Comparison

### OKLab ΔE Color Distance

```python
import numpy as np

def rgb_to_oklab(rgb):
    """Convert RGB [0-255] to OKLab perceptual space."""
    r, g, b = [x / 255.0 for x in rgb]
    
    # Linearize sRGB
    def linearize(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    
    r, g, b = linearize(r), linearize(g), linearize(b)
    
    # sRGB to XYZ
    x = 0.4123908*r + 0.357584*g + 0.180481*b
    y = 0.212639*r + 0.715169*g + 0.072192*b
    z = 0.019333*r + 0.119195*g + 0.950302*b
    
    # XYZ to OKLab
    def f(t):
        return t ** (1/3) if t > 0.008856 else 7.787*t + 16/116
    
    l = 0.210454*f(y) + 0.489308*f(x) - 0.699322*f(z)
    m = -0.090981*f(y) + 1.414556*f(x) + 0.055445*f(z)
    s = 0.035541*f(y) - 0.096414*f(x) + 0.956172*f(z)
    
    return (l, m, s)

def oklab_delta(rgb1, rgb2):
    """Perceptual color distance. ΔE < 1 = imperceptible, > 10 = obvious."""
    lab1, lab2 = rgb_to_oklab(rgb1), rgb_to_oklab(rgb2)
    return sum((a - b) ** 2 for a, b in zip(lab1, lab2)) ** 0.5
```

### Region-Based Color Extraction

```python
from PIL import Image
from collections import Counter

def extract_region_colors(img_path, regions):
    """Extract dominant color per named region.
    
    regions = {
        'top_bar': (x1, y1, x2, y2),
        'left_panel': (x1, y1, x2, y2),
        'center': (x1, y1, x2, y2),
        ...
    }
    Returns: {'top_bar': (r, g, b), ...}
    """
    img = Image.open(img_path).convert('RGB')
    results = {}
    for name, (x1, y1, x2, y2) in regions.items():
        region_pixels = list(img.crop((x1, y1, x2, y2)).getdata())
        most_common = Counter(region_pixels).most_common(1)[0][0]
        results[name] = most_common
    return results

def compare_to_spec(screenshot_colors, spec_tokens, thresholds=None):
    """Compare extracted colors against spec values.
    
    spec_tokens: {'top_bar': '#131313', 'left_panel': '#191919', ...}
    thresholds:  {'top_bar': 2.0, 'left_panel': 2.0, ...}  # OKLab ΔE
    """
    if thresholds is None:
        thresholds = {k: 2.0 for k in spec_tokens}
    
    results = {}
    for region, expected_hex in spec_tokens.items():
        if region not in screenshot_colors:
            results[region] = ('MISSING', 999, 'element not found')
            continue
        
        got = screenshot_colors[region]
        expected_rgb = hex_to_rgb(expected_hex)
        delta = oklab_delta(got, expected_rgb)
        
        threshold = thresholds.get(region, 2.0)
        if delta < threshold:
            results[region] = ('PASS', delta, f'got #{got_hex}')
        elif delta < 5.0:
            results[region] = ('WARN', delta, f'expected {expected_hex}, got #{got_hex}')
        else:
            results[region] = ('FAIL', delta, f'expected {expected_hex}, got #{got_hex}')
    
    return results

def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
```

### Output Format

```
REGION ANALYSIS:
  top_bar:    expected #131313, got #1c1c1d (ΔE=2.1) ❌ FAIL
  left_panel:  expected #191919, got #191919 (ΔE=0.0) ✅ PASS
  center:      expected #191919, got #2a2a2b (ΔE=3.2) ❌ FAIL

PASSED: 1/3, WARN: 0/3, FAILED: 2/3
SIMILARITY: 62.3%

ACTIONABLE:
  1. LeftPanel.svelte: background #1c1c1d → #131313 (ΔE=2.1)
  2. MiddlePanel.svelte: background #2a2a2b → #191919 (ΔE=3.2)
```

---

## Reference App Mismatch Detection

**Critical sanity check before comparing:**

| Reference App | HWC is a... | Valid comparison? |
|---------------|-------------|-------------------|
| Nomie / Illogical Impulse | Tiling window manager | ❌ Different purpose |
| macOS Dock | macOS-style | ❌ Different OS |
| VS Code Dark+ | Code editor | ❌ Different app type |
| Same HWC version, old state | Same | ✅ Baseline comparison |
| Wireframe/mockup | Same | ✅ Design target |

**Rule:** Confirm the reference shows the same app and purpose before doing any color comparison. A mismatch here produces a score that is meaningless in both directions.

---

## Screenshot Capture on Host

```bash
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 \
  'google-chrome-stable --headless=new \
     --disable-gpu --no-sandbox \
     --virtual-time-budget=60000 \
     --window-size=1920,960 \
     --screenshot="/tmp/hwc-qa/screenshots/v{timestamp}.png" \
     --disable-web-security \
     "http://localhost:3113"'
```

**Critical parameters:**
- `--virtual-time-budget=60000`: Svelte/React/Vue need time to render before screenshot
- `--disable-web-security`: Required for localhost/frame access
- Same `--window-size` as reference for valid comparison

---

## Thresholds Reference

| ΔE range | Interpretation | Action |
|----------|----------------|--------|
| 0.0 - 1.0 | Imperceptible difference | Accept as match |
| 1.0 - 2.0 | Slight (experts notice) | Accept for dark themes |
| 2.0 - 5.0 | Noticeable to most | Needs CSS fix |
| 5.0 - 10.0 | Obvious | Wrong color family |
| > 10.0 | Extreme | Wrong shade entirely |