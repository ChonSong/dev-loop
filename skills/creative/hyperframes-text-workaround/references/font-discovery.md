# Font Discovery for PIL Video Generation

## Problem
Standard `.ttf` font files are often NOT installed in container environments. PIL falls back to its built-in default font (~8px equivalent), which produces unreadable text at 1920×1080 resolution.

## Where to Find Fonts

### Check System Directories
```python
candidates = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
]
```

### Fallback: KaTeX Fonts (from Streamlit)
Many containerized environments have Streamlit installed, which bundles KaTeX fonts. Look in:
`/home/hermeswebui/.hermes/home/.local/lib/python3.12/site-packages/streamlit/static/static/media/`

Available fonts:
- **`KaTeX_Main-Regular.ypZvNtVU.ttf`** — serif body text (53KB, best all-purpose)
- **`KaTeX_SansSerif-Bold.CFMepnvq.ttf`** — bold sans-serif headings
- **`KaTeX_SansSerif-Regular.BNo7hRIc.ttf`** — sans-serif body text
- **`KaTeX_Typewriter-Regular.D3Ib7_Hf.ttf`** — monospace code text

### Test Font Sizes
```python
def test_font(path, text="The Garden of Automation"):
    font = ImageFont.truetype(path, 72)
    draw = ImageDraw.Draw(Image.new('RGB', (1,1), (0,0,0)))
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2]-bbox[0], bbox[3]-bbox[1]  # 72pt KaTeX: ~847x54px
```

## Readable Font Sizes at 1920x1080

| Role | Font Size | Width |
|------|-----------|-------|
| Title | 64-72px | ~800-950px |
| Subtitle | 32-36px | ~400-500px |
| Body | 24-28px | ~300-400px |
| Labels | 20-24px | ~200-300px |

## Minimum Font Size
Never go below 18px for body text at 1920x1080. Below that, text is unreadable on standard viewing.

## Downloading Fonts
If no fonts available, try:
```python
import urllib.request
urllib.request.urlretrieve(
    "https://raw.githubusercontent.com/dejavu-fonts/dejavu-fonts/master/ttf/DejaVuSans.ttf",
    "/tmp/DejaVuSans.ttf"
)
```
Note: External downloads may fail in restricted environments. Fall back to KaTeX.
