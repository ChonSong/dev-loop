# Visual QA Methodology for CSS Theme Comparison

**Problem observed:** Pixel-diff similarity scores (e.g., 81.9%) produced by PIL/pixelmatch have ZERO correlation with human perceptual similarity (~5%). These scores are meaningless for theming assessment.

## Why Pixel-Diff Fails for Theme Comparison

### Failure Modes

| Failure Mode | What Happens | Why It Breaks Assessment |
|---|---|---|
| Glassmorphism compositing | `backdrop-filter: blur()` creates semi-transparent layers. Every underlying pixel differs between reference and implementation. | Flags as massive diff even when glass layer itself is correct |
| RGB ≠ Perceptual | RGB euclidean distance doesn't model human color perception. `rgb(10,10,10)` vs `rgb(20,20,20)` is 17.3 delta but perceptually nearly identical. | Close colors flagged as mismatches, far colors may appear similar |
| Anti-aliasing | Subpixel rendering differences between captures (OS, GPU, browser version) | Flags every text edge as diff |
| Viewport mismatch | Reference captured at 1920×960, implementation at different scroll position or with different chrome included | Aggregate pixel % meaningless |
| Cropping error | Hardcoded pixel coordinates for crop regions don't match actual UI element positions | Wrong region compared |
| Dynamic content | Reference has different data visible (user names, dates, widget states) | Different pixels ≠ wrong theme |

### The 81.9% → 5% Problem Explained

The mathematical similarity (`matching_pixels / total_pixels`) measures pixel equality, NOT theme correctness. A page that is:
- 80% dark background (same color in both)
- 15% transparent/semi-transparent regions (flags as diff)
- 5% text overlays (slightly different font rendering)

...will score ~80% pixel similarity but ~0% perceptual theme similarity.

## Correct Methodology: Layered Assessment

Do NOT jump straight to screenshot comparison. Build up from the CSS layer.

### Layer 1: CSS Variable Extraction (Most Valuable)

Extract all CSS custom properties from both reference and implementation, then compare.

```javascript
// In Playwright page.evaluate():
const extractCSSVars = () => {
    const styles = getComputedStyle(document.documentElement);
    const vars = {};
    for (const prop of styles) {
        if (prop.startsWith('--')) {
            vars[prop] = styles.getPropertyValue(prop).trim();
        }
    }
    return vars;
};
const refVars = await refPage.evaluate(extractCSSVars);
const implVars = await implPage.evaluate(extractCSSVars);
```

Then compare using **perceptual color distance** (OKLab ΔE or CIE76), NOT RGB delta.

**Color distance thresholds:**
- ΔE < 1: Imperceptible
- ΔE 1-2: Perceptible through close observation
- ΔE 2-3.5: Perceptible at a glance
- ΔE > 10: Completely different color

### Layer 2: DOM Structure Comparison

Check that key themed elements exist in both DOMs:
- Sidebar / left panel
- Header / top bar
- Content area
- Footer / dock

Compare element class names, IDs, and nesting structure.

### Layer 3: Computed Style Audit

For each key element class, extract and compare computed styles:
- `background-color` / `background-image`
- `border` (width, style, color)
- `color` (text)
- `font-family`, `font-size`, `font-weight`
- `padding`, `margin`, `border-radius`

Property-level diffs are actionable. Pixel-level diffs are not.

### Layer 4: Perceptual Visual Comparison (Last Resort)

If image comparison is still needed, use:
- **SSIM** (Structural Similarity Index) — measures perceived quality
- **Butteraugli** — Google's perceptual diff tool
- **resemble.js** with `ignoreAntialiasing: true` and perceptual mode

NEVER use raw PIL pixel-diff for theme comparison.

## Viewport Standardization

| Parameter | Requirement |
|---|---|
| Viewport size | Same width × height in logical pixels |
| Device pixel ratio | Same DPR (use `fullPage: false` for consistency) |
| Browser engine | Same Chromium version |
| Scroll position | Reset to `window.scrollTo(0, 0)` before capture |
| Content state | Same login state, theme, language, test data |
| Animations | `animations: 'disabled'` in screenshot options |

## For Illogical Impulse / Nomie Themes Specifically

Illogical Impulse themes use CSS custom properties extensively:
- `--color-bg` — main background
- `--color-surface` — cards/panels
- `--color-text` — primary text
- `--color-border` — borders

The HWC vs Illogical Impulse mismatch was fundamentally a CSS variable comparison problem, not a pixel comparison problem. The HWC uses glassmorphism (`backdrop-blur-xl bg-[#12121a]/90`) while Illogical Impulse uses solid dark (`#16161e`). This is a design decision requiring human judgment, not an automated pixel-diff score.

## Decision Flow

```
Start: Compare implementation to reference design theme
  │
  ├─► Step 1: Extract CSS variables from both
  │       │
  │       ├─► Variables match (ΔE < 2) → Theme is correct at CSS level
  │       ├─► Variables close (ΔE 2-10) → Minor tweaks needed, report which
  │       └─► Variables far (ΔE > 10) → Major redesign or wrong target
  │
  ├─► Step 2: DOM structure matches? → Identify missing/extra elements
  │
  ├─► Step 3: Computed styles match at element level? → Property-level diff report
  │
  └─► Step 4: Only now — if still needed — use SSIM perceptual comparison
              with human review gate for threshold decisions
```

**Key insight:** If CSS variables match, the theme IS correct regardless of pixel-level screenshot differences. Browser rendering variations (GPU, OS, font engine) will always produce some pixel variance even for identical CSS.

## Practical Implementation

When tasked with comparing a web app UI to a reference design theme:

1. **Never start with pixel-diff** — it's the wrong tool for theming
2. **Extract CSS variables first** — this tells you exactly what colors are being used
3. **Compare color values using perceptual distance** — OKLab ΔE, not RGB delta
4. **Report design decisions separately from bugs** — glassmorphism vs solid is a design choice, not a defect
5. **Use pixel-diff only for regression** — "did this build break something that worked yesterday?"