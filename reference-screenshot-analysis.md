# GTO Wizard Reference Screenshot Analysis

**Directory:** `/home/sc/repos/gto-wizard-clone/docs/`
**Total PNG files:** 12
**Generated:** June 26, 2026

---

## Summary of Findings

The 12 reference screenshots fall into 6 distinct layout groups based on pixel-level analysis:

### Group 1: Dashboard / Practice / Equity / ICM / Courses / Trainer (Similar nav layout)
**Dimensions:** 800×576px
**Shared chrome:** Dark background (#09090C to #1D1D1D), left navigation sidebar with green active state indicators.

---

## Detailed Image Descriptions

### 1. `reference-dashboard.png` (800×576, RGB)

**Layout Structure:**
- **Background:** True black (#09090C) at very top/bottom edges, quickly transitioning to dark gray (#1D1D1D) for the main content area
- **Header:** Minimal top bar at y=0-49, background color #1D1D1D (dark gray), no bright content visible
- **Left Sidebar (~x=0-120):** 
  - Dark background (#1D1D1D)
  - Navigation items rendered as green colored blocks:
    - Active/selected nav items: Bright green RGB(170, 251, 178) - a neon/lime green (#AAFBB2)
    - Text labels appear in light gray (#BBBBBB) and white (#FFFFFF)
  - Three green navigation blocks visible: around y=60-80, y=175-205, y=320-370 (bottom section)
  - Light text at y=115-155, y=460, y=525, y=540
- **Main Content Area (x>120):**
  - Card/list grid area with green background elements:
    - Rows 60-81: Scattered green pixels (header area highlight)
    - Rows 171-202: Green accent (nav item background, ~59 px tall)
    - Rows 310-367: Largest green region (main content cards, ~57 rows)
    - Rows 530-564: Bottom green section
  - White text regions at:
    - Rows 116-124 (card titles)
    - Rows 137-148 (card subtitles)
    - Rows 281-290
    - Rows 335-346 (largest text block)
    - Rows 449-460
    - Rows 497-507
    - Rows 520-563 (bottom statistics/comments area)

**Colors:**
- Primary background: #09090C → #1D1D1D
- Active/bright green: #AAFBB2 (RGB 170, 251, 178)
- Text: White (#FFFFFF) and light gray (#BBBBBB)
- Cards/sections: Very dark gray with green accents

**Key Design Notes:**
- No red or blue in this view
- The green is very saturated and bright - a lime/neon green
- Navigation uses pill-shaped green indicators
- Content appears to be in a card grid or list view

---

### 2. `reference-courses.png`, `reference-equity.png`, `reference-icm.png` (ALL 800×576, RGB) — PIXEL IDENTICAL

These three images are **pixel-perfect identical** based on sampling analysis. They share:
- Same color distribution: 86.6% black, 4.1% #202020, 2.3% #404040, 1.6% green (#A0E0A0)
- Same light text regions at identical y-positions
- Same green block positions
- This suggests they are the **same page template** with only the title/label text differing (the difference would be in the HTML content rendered at different times)

**What this tells us about the template:**
- A reusable dark-themed card grid page
- Sidebar with green active indicators at y=60-80, y=175-205, y=320-370
- Three content sections in the main area
- Card rows with header + subtitle text

---

### 3. `reference-practice.png` & `reference-trainer.png` (800×576, RGB) — PIXEL IDENTICAL

These two images are also **pixel-perfect identical** to each other but different from group above.

**Distinctive differences from Dashboard:**
- Slightly lighter header: RGB(18, 18, 18) instead of (9, 9, 12) at top
- Left sidebar at y=200 shows RGB(150, 150, 150) - a gray active state instead of green
- Bottom area has blue-green tint at y=450: RGB(31, 84, 104) - a teal color
- Green felt/poker table appearance appearing in content area:
  - Rows 189-203: Subtle green pixels
  - Rows 325-359: More prominent green content area
- Text regions fundamentally different:
  - Rows 196-224: Large text block (64px wide)
  - Rows 255-283: Large text block (77px wide)
  - Rows 429-440, Rows 527-535: Smaller text
- No bright green (#AAFBB2) - instead has muted green content
- Dominant colors: 80.4% black, 5.1% deep teal (#002020), 3% dark gray

**Interpretation:** These are a practice/trainer mode with a poker table visualization in the center area.

---

### 4. `reference-solutions.png` & `reference-study.png` (800×576, RGB) — PIXEL IDENTICAL

These are the most content-rich screenshots - showing a **game tree with heatmap**.

**Layout Structure:**
- **Background:** Dark gray (#121212 to #2F2F2F), lighter than the dashboard
- **Top area (y=0-56):** 
  - Contains a gradient from #121212 → #6E6E6E (at y=20) → back to #2F2F2F
  - This is likely a game tree visualization with colored overlay
- **Game Tree Structure (visible from color analysis):**
  - **Red elements** at x=50-461, rows 63-535: This is decision/action nodes (RGB 240, 60, 60 = #F03C3C)
  - **Blue elements** at x=311-461/715, rows 99-535: Opponent action nodes (RGB 61, 124, 184 = #3D7CB8)
  - **White separators** between tree levels (rows 126, 150, 192, 260, 300, 370, 520)

**Tree Node Map:**
```
y=70:   ROOT RED (x=50-461) - "Limp/Raise ?" decision node
y=90:   ROOT RED continues
y=100:  SPLIT: RED (x=50-355) + BLUE (x=311-461) branches
y=130:  RED expands to full width (50-737) + BLUE wide (311-715)
y=150:  White separator line
y=170:  BLUE continues only (x=50-upper range)
y=210:  BLUE at full width (158 px wide)
y:250:  BLUE at max intensity (158 px wide)
y=260:  White separator
y=270:  BLUE narrower (32 px wide) → branches becoming finer
y=300:  WHITE separator
y=310:  Fine BLUE lines (tree depth increasing)
y=350:  BLUE + small RED wedges (16-24 px) showing mixed strategy
y=370:  WHITE separator
y=390:  RED + BLUE at similar widths (mixed strategy display)
y=410:  WHITE separator  
y=430:  RED 34px + BLUE 156px (heavy blue/raise favored)
y=450+: Same pattern continues (blue dominates)
y=540:  Footer/dark area
```

**Vertical axis (y):**
- y=335-348: Green highlight (44 green px wide) - likely an EV/equity indicator bar
- Below y=550: Dark (#121212 to #272727)

**Colors used:**
- Red (action/raise): #F03C3C (RGB 240, 60, 60)
- Blue (call/fold/limp): #3D7CB8 (RGB 61, 124, 184)
- White separators: #FFFFFF at ~50% opacity/width
- EV/Green indicator: Scattered green pixels at y=335-343

**This is a strategy solutions page showing:**
1. A game tree (top portion, rows 63-310)
2. A strategy distribution chart (rows 310-540) showing red/blue mixed strategy bars
3. The tree reads left-to-right with decision splits

---

### 5. `reference-study-interface.png` (2367×290, RGBA)

**Layout:** Ultra-wide banner/strip (4:1 aspect ratio)

**Analysis:**
- **Background:** Predominantly dark (#000000 to #1D1D1D)
- **Content area:** Rows 92-138 show a single line of light text (28px wide max)
- Total non-dark rows: 273 out of 290 (most of the 290px height has some content)
- This appears to be a **mobile phone mockup or narrow viewport capture** of the study interface, or more likely a **responsive design at a specific breakpoint**
- The wide, short dimension suggests it could be a **horizontal scrolling game state selector** or a **top navigation header strip** shown in a narrow mobile view
- Left column shows dark background (#1C1C1C) with a single content cluster at y=100

**Colors:**
- 61.7% black, 21.4% #202020, 5.8% #404040
- Very sparse UI - likely a truncated/mobile view

---

### 6. `screenshot-live-study-preflop.png` (1440×900, RGB)

This is a **live application screenshot** at full resolution showing the actual poker study interface.

**Layout Structure:**
- **Background:** Pure black (#0A0A0A) at top, #111111 below
- **Green felt area** starting at y=9: Bright green pixels (RGB 0, 200, 83 = #00C853) extending to y=287
  - This is the poker table felt
  - Peak green at rows 9-41 (89 green px/row = full-width green felt header)

**Top toolbar indicators:**
- x=40, y=15-35: Green icon (#00C853) - possibly a back/home button
- x=280-520: Gray icons (#727272, #969696) - navigation/control elements  
- x=640-680: Green text (#00A660) - secondary indicator
- x=920: Green (#00C853)
- x=1000-1080: Gray text (#6F6F6F, #5D5D5D)
- x=1360-1400: Green (#00B74F) or white - settings/profile area

**Game play area:**
- y=249: White card (28px wide pixel detected) - **playing cards visible**
- y=300: Red element (RGB 211, 47, 47 = #D32F2F) starting - action indicator
- y=350-550: Red gradient from #C12D2D to #B12B2B - a **heatmap overlay** on the poker table
  - This deep red covers the center-right area (~x=540+, y=300-800)
  - Indicates frequency/heat visualization

**ActionButton area (y=750-860):**
- y=750-790: Large red action button at x=540-600 (RGB 190, 44, 44)
- x=600-630: Red button at y=780+ (RGB 170, 42, 42 = #EA2A2A) - "FOLD" or similar?
- These are large poker action buttons (Fold, Call, Raise)

**Left sidebar at full resolution:**
- y=250: White nav (#FFFFFF) - active top item
- y=300: White + red highlight (#D32F2F) - active item with badge
- y=350+: Red items (#BD2D2D, #B62C2C, etc.) - deck/study items with red accent
- Portrait-oriented navigation with icons and text

---

### 7. `screenshot-live-study-preflop-v2.png` (1440×900, RGB)

Nearly identical to v1 with slight differences:
- Same green felt at y=9 (#00C853)
- Same action buttons at y=750+ 
- Heatmap red elements slightly different
- No white navigation at y=250 (darker)
- Slightly less gray content at top (more dark)

---

### 8. `screenshot-live-study-preflop-v3.png` (1440×900, RGB)

Nearly identical to v1 and v2:
- Identical green felt header
- Action buttons at y=750 region
- Slightly different heatmap distribution
- Bottom area (y=857-865) shows white text (study notes?)

---

## Key Colors Identified Across All Images

| Color | Hex | RGB | Usage |
|-------|-----|-----|-------|
| Background (dark) | #09090C | 9, 9, 12 | Page background |
| Background (gray) | #121212 | 18, 18, 18 | Content area bg |
| Background (mid) | #1D1D1D | 29, 29, 29 | Sidebar bg |
| Bright Green | #00C853 | 0, 200, 83 | Active felt/buttons |
| Lime Green nav | #AAFBB2 | 170, 251, 178 | Nav active state |
| Dark Green | #00A660 | 0, 166, 96 | Secondary green |
| Poker Red | #F03C3C | 240, 60, 60 | Action node (tree) |
| Muted Red | #D32F2F | 211, 47, 47 | Heatmap light |
| Deep Red | #B12B2B | 177, 43, 43 | Heatmap dark |
| Action Button | #BE2C2C | 190, 44, 44 | Bet/raise button |
| Action Button 2 | #EA2A2A | 234, 42, 42 | Call/fold button |
| Strategy Blue | #3D7CB8 | 61, 124, 184 | Call/fold node |
| White text | #FFFFFF | 255, 255, 255 | Primary text |
| Light Gray | #BBBBBB | 187, 187, 187 | Secondary text |
| Teal accent | #1F5468 | 31, 84, 104 | Practice/trainer accent |

## UI Element Sizing

- **Sidebar width:** ~120-130px
- **Header height:** ~50px
- **Action buttons:** ~60px wide × ~80px tall (at 1440px viewport)
- **Poker cards:** ~28px pixel clusters (needs higher-res analysis)
- **Game tree levels:** ~20-30px vertical spacing between decision nodes
- **Strategy bars:** ~30px vertical per action line

## Typography Notes

- Text renders as anti-aliased white/gray on dark background
- Navigation labels: Medium weight, ~10-12px effective size at 800px viewport
- Card/action labels: Bold, white
- Statistics: Light gray, smaller size
- The light text regions show single-pixel-width characters (likely 11-14px system font)

## Responsive Behavior

- 800×576 screenshots: Desktop/tablet view with sidebar visible
- 1440×900 screenshots: Full desktop with wider game area
- 2367×290: Either mobile landscape or a horizontal strip component
