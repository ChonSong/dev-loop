#!/usr/bin/env python3
"""
composite_subject.py — Composite a foreground subject (with alpha) onto a background image.

Usage:
    python3 composite_subject.py <subject.png> <background.jpg> [--style ghibli|disney|none] [--output result.png]

The subject must be RGBA with transparent background (use rembg first).
"""
import sys, os
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw

STYLES = {}

def ghibli_grade(img):
    img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
    img = ImageEnhance.Color(img).enhance(1.3)
    r, g, b = img.split()
    r = r.point(lambda i: min(255, int(i * 1.08)))
    g = g.point(lambda i: min(255, int(i * 1.02)))
    b = b.point(lambda i: max(0, int(i * 0.92)))
    img = Image.merge("RGB", (r, g, b))
    img = ImageEnhance.Contrast(img).enhance(1.1)
    blur = img.filter(ImageFilter.GaussianBlur(radius=3))
    return Image.blend(img, blur, 0.15)
STYLES["ghibli"] = ghibli_grade

def disney_grade(img):
    img = ImageEnhance.Color(img).enhance(1.5)
    img = ImageEnhance.Brightness(img).enhance(1.1)
    img = ImageEnhance.Contrast(img).enhance(1.15)
    r, g, b = img.split()
    r = r.point(lambda i: min(255, int(i * 0.98)))
    b = b.point(lambda i: min(255, int(i * 1.1)))
    img = Image.merge("RGB", (r, g, b))
    blur = img.filter(ImageFilter.GaussianBlur(radius=5))
    return Image.blend(img, blur, 0.12)
STYLES["disney"] = disney_grade

def resize_and_crop_cover(bg, target_size):
    tw, th = target_size
    bw, bh = bg.size
    scale = max(tw / bw, th / bh)
    bg = bg.resize((int(bw * scale), int(bh * scale)), Image.LANCZOS)
    left = (bg.width - tw) // 2
    top = (bg.height - th) // 2
    return bg.crop((left, top, left + tw, top + th))

if __name__ == "__main__":
    args = sys.argv[1:]
    subject_path = args[0] if len(args) > 0 else "no_bg.png"
    bg_path = args[1] if len(args) > 1 else "background.jpg"
    style = "none"
    output = "composite.png"

    for i, a in enumerate(args):
        if a == "--style" and i + 1 < len(args):
            style = args[i + 1]
        if a == "--output" and i + 1 < len(args):
            output = args[i + 1]

    subject = Image.open(subject_path).convert("RGBA")
    bg = Image.open(bg_path).convert("RGB")
    bg = resize_and_crop_cover(bg, subject.size)

    if style in STYLES:
        bg = STYLES[style](bg)

    result = Image.new("RGBA", subject.size, (0, 0, 0, 0))
    result.paste(bg, (0, 0))
    result = Image.alpha_composite(result, subject)
    flat = Image.new("RGB", result.size, (255, 255, 255))
    flat.paste(result, mask=result.split()[3])
    flat.save(output, quality=95)
    print(f"Saved: {output} ({os.path.getsize(output):,} bytes)")
