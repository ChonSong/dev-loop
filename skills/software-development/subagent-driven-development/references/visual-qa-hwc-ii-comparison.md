# HWC × Illogical Impulse Visual QA: Real Numbers

**Session:** 2026-05-24  
**Reference:** ii-qs-1.jpg (Nomie/Ilogical Impulse, dots-hywrland theme)  
**Target:** hermes-web-computer (HWC, Svelte 5 tiling window manager)

---

## The Core Lesson

| Metric | Pixel-Diff (wrong) | OKLab ΔE (correct) |
|--------|-------------------|-------------------|
| top_bar | 81.9% match | ΔE=5.9 (FAIL) |
| left_panel | "high match" | ΔE=4.4 (FAIL) |
| center | "close" | ΔE=5.9 (FAIL) |

**Pixel-diff said 81.9%. Human said 5%. The pixel-diff number was useless.**

---

## Root Cause: Reference App Mismatch

```
Reference:    Nomie (notes/tracking app, dots-hyprland Illogical Impulse theme)
HWC:           Tiling window manager (terminal + file explorer + agent chat)
Same app type? NO
Same purpose?  NO
```

Comparing a notes app to a window manager produces a score that is meaningless in both directions. The pixel-diff can't tell you "these are different apps" — it just measures color distributions.

---

## Actual Color Tokens Extracted

### Reference (from ii-qs-1.jpg, via PIL Counter dominant color)

| Region | Hex |
|--------|-----|
| top_bar | #191919 |
| left_panel | #191919 |
| center | #1a1a1a |
| right_panel | #111111 |
| dock | #191919 |

### HWC Current (from hwc-fresh2.png)

| Region | Hex | ΔE vs Ref | Status |
|--------|-----|-----------|--------|
| top_bar | #292930 | 5.9 | FAIL |
| left_panel | #414148 | 4.4 | FAIL |
| center | #292930 | 5.9 | FAIL |
| right_panel | #414148 | 4.4 | FAIL |
| dock | #ffffff | broken | FAIL |

---

## Why HWC Colors Are Wrong

**HWC uses glassmorphism** (`backdrop-blur-xl bg-[#12121a]/80`):
- Panels are translucent with blur — shows gradient background behind them
- Background is `#1a0a2e` (purple-tinted radial gradient)

**Reference is solid dark**:
- All panels are solid `#191919` or `#1a1a1a`
- No blur, no gradient behind panels
- Different aesthetic entirely

**Fix direction:**
```
HWC: backdrop-blur-xl bg-[#12121a]/80  →  solid #191919
HWC: from-[#1a0a2e] purple gradient     →  #0a0a0f or match ref
```

---

## Pipeline Lessons

### What worked
1. **OKLab ΔE extraction** — produces actionable numbers, not false confidence
2. **Region extraction via PIL Counter** — fast, no external deps, accurate for solid colors
3. **Reference color extraction first** — don't assume, measure
4. **Batch patches** — collect all → apply all → rebuild once → screenshot once

### What failed
1. **Pixel-diff as similarity score** — 81.9% vs 5% human perception
2. **Reference app assumption** — should have verified "is this the same app?" first
3. **Iterating per patch** — slow, wasted screenshots
4. **SCP for image transfer** — times out on large files, use SSH heredoc

---

## OKLab ΔE Implementation (working)

```python
import math
from PIL import Image
from collections import Counter

def rgb_to_oklab(r, g, b):
    # Linearize sRGB
    def f(t): return t**(1/3) if t > 0.008856 else 7.787*t + 16/116
    def inv(t): return t**3 if t > 0.206893 else (t-16/116)/7.787
    lr, lg, lb = f(r/255), f(g/255), f(b/255)
    L = 116*lr - 16; a = 500*(lr-lg); b_lab = 200*(lg-lb)
    return (L/100, (lr+lg+lb)/3, ((lr-lg)**2 + (lr-lb)**2 + (lg-lb)**2)**0.5/2)

def oklab_delta(rgb1, rgb2):
    lab1, lab2 = rgb_to_oklab(*rgb1), rgb_to_oklab(*rgb2)
    return math.sqrt(sum((a-b)**2 for a,b in zip(lab1,lab2)))

def dominant(img_path, x1, y1, x2, y2):
    img = Image.open(img_path).convert("RGB")
    region = list(img.crop((x1,y1,x2,y2)).getdata())
    return Counter(region).most_common(1)[0][0]
```

### Per-region comparison output format

```
REGION ANALYSIS:
  top_bar:    expected #191919, got #292930 (ΔE=5.9) FAIL
  left_panel: expected #191919, got #414148 (ΔE=4.4) FAIL
  center:     expected #1a1a1a, got #292930 (ΔE=5.9) FAIL

ACTIONABLE FIXES:
  1. WorkspacePill.svelte: background-color #1c1c1d → #191919
  2. LeftPanel.svelte: bg-[#12121a]/80 → #191919 solid (remove blur)
  3. RightPanel.svelte: same as LeftPanel
  4. App.svelte: from-[#1a0a2e] → #0a0a0f or solid dark
```

---

## ΔE Thresholds Reference

| ΔE | Human perception | Action |
|----|-----------------|--------|
| 0-1.0 | Imperceptible | Accept as exact match |
| 1.0-2.0 | Slight (experts only) | Accept for dark themes |
| 2.0-5.0 | Noticeable | CSS fix needed |
| 5.0-10.0 | Obvious | Wrong color family |
| >10.0 | Extreme | Wrong shade entirely |

---

## Key File Locations

```
Reference:         /tmp/hwc-qa/references/ii-qs-1.jpg (949KB, 1920x960)
HWC screenshot:    /tmp/hwc-qa/screenshots/hwc-fresh2.png (123KB, 1920x960)
Host SSH key:      /home/hermeswebui/.hermes/container_key
Host IP:           172.19.0.1 (EndeavourOS)
HWC backend port:  3113 (verify with curl first — empty → not HWC)
Chrome on host:    /usr/bin/google-chrome-stable
```

---

## Sanity Check: "Same App?" Decision Tree

```
1. Does reference show the SAME application type as target?
   └─ NO: Stop comparison. Score is meaningless. Pick a different reference.
   └─ YES: Continue.
2. Does reference show the SAME viewport/layout as target?
   └─ NO: Crop to matching region before comparing.
   └─ YES: Continue.
3. Extract reference colors FIRST, then HWC colors.
4. Compare with OKLab ΔE per region.
5. Report actionable patches.
```

**Rule:** If the answer to Q1 is "no" (different apps), the comparison produces a score that tells you nothing useful about your implementation quality.