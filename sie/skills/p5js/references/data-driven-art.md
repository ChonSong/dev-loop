# Data-Driven Generative Art — Cross-Skill Reference

> This file is a reference for the `creative/p5js` skill. It captures patterns from
> sessions combining p5.js generative art with personal data visualization.

## Parallel Execution Pattern
When data acquisition is pending (file upload, API fetch, etc.):
1. Generate placeholder/mock data with realistic statistical distributions
2. Build ALL art code against placeholder data — don't block on data
3. Swap placeholder → real data via `loadJSON()` or file replacement
4. User sees progress immediately; iterate on visuals while data transfers

## Data Pipeline for Personal Data (e.g., Browsing History)
1. **Parse** raw export (History.json, CSV) → structured records
2. **Categorize** via regex on domain names (social/dev/news/shopping/entertainment/finance/education/travel/other)
3. **Enrich**: visit frequency, recency, time-of-day distribution, session clustering (30-min gap threshold)
4. **Encode** visual properties:
   - Position → time (radial: center=old, outer=new)
   - Size → log(visit_count) — never raw count
   - Color → category (HSB: category→hue, vary S/B for depth)
   - Opacity → recency (recent=1.0, oldest=0.3)
5. **Exclude** sensitive domains via pattern list

## Complementary Skills
| Skill | Use Case |
|-------|----------|
| `pixel-art` | Retro mosaic variants (treemap/shelf/spiral layouts + Floyd-Steinberg dithering) |
| `hyperframes` | HTML→MP4 video (GSAP timeline, lint→validate→render pipeline) |
| `design-md` | Shared design token spec across all output variants |
| `D3.js` (no skill) | Interactive force-graph explorer (hover tooltips, time slider, search) |

## Standard Output Matrix
Per art style, generate:
- **Static:** 4K PNG (3840×2160), Puppeteer headless
- **Animation:** MP4 (30fps, 15-30s), CCapture.js or HyperFrames
- **Interactive:** HTML (D3.js or p5.js), hover/explore

## Visual Patterns That Work
- **Neural Constellation:** Radial time rings + bloom glow + bezier connections + vignette
- **Digital Aurora:** Curl noise flow field + category attractors + trail accumulation + ADD blending
- **Pixel Mosaic:** Treemap layout + arcade palette (16 colors, 8px) + Floyd-Steinberg dithering
- **D3 Force Atlas:** Category clustering + session co-occurrence links + SVG glow filter

## Design Principles for Dark Canvas Work
- Never use `background(0)` or `background(255)` — always gradient + noise texture
- HSB color mode mandatory for generative art
- `pixelDensity(1)` + `p5.disableFriendlyErrors = true` before setup()
- Seeded randomness: `randomSeed()` + `noiseSeed()` for reproducibility
- Bloom glow: downsample → blur → ADD composite
- Trail accumulation: fade rect alpha 5-15, stroke alpha 80-120 (high enough to persist)
