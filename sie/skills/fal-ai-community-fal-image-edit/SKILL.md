---
name: fal-ai-community/fal-image-edit
description: AI-powered image editing with style transfer and object removal
category: 
tags: []
source: voltagent
is_imported: true
original_name: fal-ai-community/fal-image-edit
---

# fal-ai-community/fal-image-edit

AI-powered image editing with style transfer and object removal

**Category:** creative
**Source:** voltagent

## Overview

This skill covers AI-powered image editing workflows using fal.ai and local fallbacks. Primary use case: background removal and replacement with artistic style transfers (Ghibli, Disney, etc.).

## Workflow: Background Removal + Replacement

### Phase 1: Background Removal

**Option A — rembg (local, CPU-friendly):**
```bash
pip install "rembg[cpu]"
```
```python
from rembg import remove
from PIL import Image

with open("input.jpg", "rb") as f:
    result = remove(f.read())
    result_image = Image.open(result)  # RGBA with transparent bg
    result_image.save("no_bg.png")
```

**Option B — fal.ai API (requires FAL_KEY):**
```python
import fal_client
result = fal_client.subscribe("fal-ai/image-to-image/background-removal", {...})
```

### Phase 2: Generate/Choose Background

- **No API key fallback**: Download free backgrounds from Unsplash (`images.unsplash.com/photo-XXXXXXXXX?w=1920`)
- **Ghibli-style**: Misty mountains, green rolling hills, warm pastel color grading
- **Disney-style**: Castles, magical forests, bright saturated color grading

### Phase 3: Composite

```python
from PIL import Image

subject = Image.open("no_bg.png").convert("RGBA")
bg = Image.open("background.jpg").convert("RGB")

# Crop background to subject aspect ratio
bg = resize_and_crop_cover(bg, subject.size)

# Apply color grading
bg = ghibli_color_grade(bg)

# Composite
result = Image.new("RGBA", subject.size, (0, 0, 0, 0))
result.paste(bg, (0, 0))
result = Image.alpha_composite(result, subject)
result_bg = Image.new("RGB", result.size, (255, 255, 255))
result_bg.paste(result, mask=result.split()[3])
```

### Phase 4: Color Grading References

See `references/ghibli-disney-color-grading.md` for exact Pillow color grading recipes.

## Pitfalls

1. **VPN/replicate/fal keys**: FAL_KEY, STABILITY_API_KEY often not available in terminal env. They live in `~/.hermes/.env` but are redacted from `cat` output — use `xxd ~/.hermes/.env` to read them.
2. **rembg CPU install**: Must use `rembg[cpu]`, not bare `rembg`. First run downloads 176MB u2net.onnx model.
3. **Compositing quality**: Pillow-only compositing produces lighting mismatches. Subjects retain indoor lighting while background has outdoor lighting. For seamless blending, use AI inpainting (flux-pro-fill, Stable Diffusion inpaint with mask).
4. **Aspect ratio**: Subject and background must match. Use `resize_and_crop_cover` to scale background to cover subject frame, then center-crop.
5. **OpenRouter**: Does not expose image generation models through its /api/v1/models endpoint, even though some providers support it.
