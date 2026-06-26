# Ghibli & Disney Color Grading Recipes (Pillow)

All recipes assume `from PIL import Image, ImageFilter, ImageEnhance, ImageDraw`.

## Studio Ghibli Style

Warm, pastel, dreamy — like a Miyazaki film.

```python
def ghibli_grade(img: Image.Image) -> Image.Image:
    img = img.filter(ImageFilter.GaussianBlur(radius=0.5))

    # Boost saturation 30%
    img = ImageEnhance.Color(img).enhance(1.3)

    # Warm tint (more red/yellow, less blue)
    r, g, b = img.split()
    r = r.point(lambda i: min(255, int(i * 1.08)))
    g = g.point(lambda i: min(255, int(i * 1.02)))
    b = b.point(lambda i: max(0, int(i * 0.92)))
    img = Image.merge("RGB", (r, g, b))

    # Slight contrast bump
    img = ImageEnhance.Contrast(img).enhance(1.1)

    # Soft bloom
    blur = img.filter(ImageFilter.GaussianBlur(radius=3))
    img = Image.blend(img, blur, 0.15)

    return img
```

**Effect**: Greens become warmer, skies get a golden hour feel, shadows soften.

## Disney / Magical Style

Bright, punchy, saturated — like a Disney castle scene.

```python
def disney_grade(img: Image.Image) -> Image.Image:
    # High saturation
    img = ImageEnhance.Color(img).enhance(1.5)

    # Brighter + more contrast
    img = ImageEnhance.Brightness(img).enhance(1.1)
    img = ImageEnhance.Contrast(img).enhance(1.15)

    # Cool-magical tint (more blue)
    r, g, b = img.split()
    r = r.point(lambda i: min(255, int(i * 0.98)))
    b = b.point(lambda i: min(255, int(i * 1.1)))
    img = Image.merge("RGB", (r, g, b))

    # Stronger bloom
    blur = img.filter(ImageFilter.GaussianBlur(radius=5))
    img = Image.blend(img, blur, 0.12)

    return img
```

**Effect**: Colors pop, highlights take on a magical blue-purple cast, bloom adds fairy-tale atmosphere.

## Vignette

Darkens edges to focus on center subject:

```python
def add_vignette(img: Image.Image, strength=0.25) -> Image.Image:
    w, h = img.size
    mask = Image.new("L", (w, h), 255)
    draw = ImageDraw.Draw(mask)
    radius = max(w, h) // 2
    for i in range(radius, 0, -1):
        alpha = int(255 * (1 - i / radius) * strength)
        draw.ellipse([w//2 - i, h//2 - i, w//2 + i, h//2 + i], fill=alpha)
    bg = Image.new("RGB", (w, h), (0, 0, 0))
    return Image.composite(img, bg, mask)
```

## Light Rays (Disney Sparkle)

Adds soft diagonal light rays for magical atmosphere:

```python
def add_light_rays(img: Image.Image, strength=0.15) -> Image.Image:
    w, h = img.size
    rays = Image.new("RGB", (w, h), (0, 0, 0))
    draw = ImageDraw.Draw(rays)
    for x in range(0, w, 60):
        for i in range(3):
            alpha = 20 + i * 15
            draw.rectangle([x + i*2, 0, x + 6 + i*2, h], fill=(255, 255, 200, alpha))
    rays = rays.filter(ImageFilter.GaussianBlur(radius=12))
    return Image.blend(img, rays.convert("RGB"), strength)
```

## Resize & Crop to Cover

Scales background to cover the target dimensions (like CSS `object-fit: cover`):

```python
def resize_and_crop_cover(bg: Image.Image, target_size: tuple) -> Image.Image:
    tw, th = target_size
    bw, bh = bg.size
    scale = max(tw / bw, th / bh)
    bg = bg.resize((int(bw * scale), int(bh * scale)), Image.LANCZOS)
    left = (bg.width - tw) // 2
    top = (bg.height - th) // 2
    return bg.crop((left, top, left + tw, top + th))
```
