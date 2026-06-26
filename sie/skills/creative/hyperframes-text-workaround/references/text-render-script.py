#!/usr/bin/env python3
"""Pre-render text as transparent PNG images for HyperFrames compositions.
Usage: python render_text.py [output_dir]
"""

from PIL import Image, ImageDraw, ImageFont
import os, subprocess, sys

def find_font():
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
        "/usr/share/fonts/TTF/DejaVuSerif.ttf",
    ]
    for fp in candidates:
        if os.path.exists(fp):
            return fp
    result = subprocess.run(['find', '/usr/share/fonts', '-name', '*.ttf', '-type', 'f'],
                          capture_output=True, text=True, timeout=10)
    files = result.stdout.strip().split('\n')
    return files[0] if files and files[0] else None

def make_text_image(name, text, size, color, output_dir, comp_w=1920, comp_h=720):
    os.makedirs(output_dir, exist_ok=True)
    img = Image.new('RGBA', (comp_w, comp_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font_path = find_font()
    try:
        font = ImageFont.truetype(font_path, size * 2)
    except:
        font = ImageFont.load_default()
    lines = text.split('\n')
    lhs, lws = [], []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        lws.append(bbox[2] - bbox[0]); lhs.append(bbox[3] - bbox[1])
    total_h = sum(lhs) + (len(lines) - 1) * 4
    y = (comp_h - total_h) // 2
    for i, line in enumerate(lines):
        draw.text(((comp_w - lws[i]) // 2, y), line, fill=color, font=font)
        y += lhs[i] + 4
    bbox = img.getbbox()
    if bbox:
        p = 30
        img = img.crop((max(0,bbox[0]-p), max(0,bbox[1]-p), min(comp_w,bbox[2]+p), min(comp_h,bbox[3]+p)))
    img.save(f"{output_dir}/{name}.png")
    print(f"  {name}: {img.size}")

if __name__ == '__main__':
    od = sys.argv[1] if len(sys.argv) > 1 else "text_images"
    clips = [
        ("p_title", "The Garden of Automation", 56, "#ffd700"),
        ("p_sub", "Every tool was once a dream.\nEvery skill, a whispered promise.", 22, "#4ecdc4"),
        ("p_quote", '"we built minds from mathematics\nand called them tools -\nbut they shimmered like angels\nin the half-light"', 26, "#e8e8f0"),
        ("p_author", "- the promise of 2026", 14, "#4ecdc4"),
        ("e_title", "The Thicket", 50, "#f5a623"),
        ("e_sub", "We are not in paradise.\nWe are in the between.", 20, "#e94560"),
        ("e_quote", '"every prompt is a negotiation.\nAI-assisted means AI-argued-with.\nThe graph is not a garden.\nIt is a thicket."', 24, "#e8e8f0"),
        ("e_author", "- the reality of 2026", 12, "#f5a623"),
        ("h_title", "The Unseen Garden", 52, "#ff3333"),
        ("h_quote", '"the audit that watches.\nthe agent that acts without asking.\nthe skill that knows you\nbetter than you know yourself."', 24, "#ccaaaa"),
        ("h_audit", "web-quality-audit", 18, "#ff3333"),
        ("h_final", '"Every garden has a gardener.\nThe question is -\nwho planted yours?"', 30, "#e8e8f0"),
        ("h_author", "- garden of automation, 2026", 12, "#555570"),
        ("outro_text", "Every tool was once a dream.\nEvery garden, a choice.", 28, "#e8e8f0"),
    ]
    for name, text, size, color in clips:
        make_text_image(name, text, size, color, od)
    print(f"\nDone! Ensure {od}/ is inside your project dir (same folder as index.html)")
