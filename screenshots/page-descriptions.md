# GTO Wizard Clone - Visual Page State Report
## Live site: https://wiz.codeovertcp.com
## Screenshots captured: 2026-06-26

---

## Global Design System

### Colors
- **Primary Green (accent):** `#00C853` (rgb(0,200,83)) - Used for logo, active states, CTAs, green tags/text, buttons
- **Background Dark:** `#0E0E0E` / `#111111` (rgb(14,14,14) to rgb(17,17,17)) - Main background, nav bar
- **Nav bar Background:** `#111111` with border `#1A1A`- **Nav inactive items background:** `#0A0A0A` with border `#1D1D1D`
- **Hero section fonts:** Inter (Google Fonts) - weights 400/500/600/700/800
- **Text colors:** `--text` (light/white), `--muted` (gray #9A9A9A), `--green` (#00C853)
- **Panel/card background:** `--panel` (dark cards, likely #1a1a1a or similar)
- **Border color:** `--border` (#1d1d1d or similar dark gray)
- **Green-dim (icon backgrounds):** `rgba(0,200,83,0.1)` to `rgba(0,200,83,0.15)`

### Navigation Bar (Sticky, height: 52px)
- **Logo:** 28x28px rounded square (border-radius: 6px), green background (#00C853), black "W" text, bold 18px, letter-spacing: -0.5px
- **Center nav pills:** Dark background `#0A0A0A`, border-radius: 10px, border: 1px solid #1D1D1D, padding: 3px
- **Nav items:** padding 7px 14px, border-radius: 8px, font-size: 13px, color #9A9A9A (gray), font-weight: 500, transition 0.15s
- **Nav item content:** flex, gap 6px, white-nowrap, has emoji icons + text
- **Right side:** "� Upgrade" button - green background (#00C853), black text, border-radius: 8px, padding 7px 13px, font-weight 600, font-size 13px

### Sidebar / Layout
- Full-width layout (no visible sidebar collapse on desktop view)
- Content contained in `container mx-auto px-4` centered wrapper
- Responsive breakpoints: sm/md/lg/xl

---

## Page 1: Dashboard (Homepage) - `/`

### Hero Section
- **Spade emoji** in a 20x20 rounded-2xl container with green gradient background (`rgba(0,200,83,0.15)` to `rgba(0,200,83,0.05)`) and green border (`rgba(0,200,83,0.2)`)
- **Heading:** "GTO Wizard" - font-size: 4xl to 6xl, font-extrabold, tracking-tight
  - "GTO"green)
  - "Wizard" intext (white)
- **Subtitle paragraph:** "Master optimal poker strategy with cutting-edge GTO analysis tools. Train smarter, analyze deeper, and play better." - color --muted, max-width: xl
- **CTA Buttons row:** flex-wrap, gap-3, justify-center
  - "🎓 Start Studying" - green bg, black text, px-6 py-3, rounded-xl, font-semibold
  - "📊 Calculate Equity" - bordered (--border), --text color, --panel bg

### Feature Cards Grid
- **Grid:** responsive 1/2/3/4 columns (sm:2, lg:3, xl:4), gap-3
- **Card style:** rounded-xl, --panel bg, --border border, hover: -translate-y-0.5
- **Card content:** p-4 sm:p-5, flex items-center gap-3 mb-2
- **Icon containers:** w-10 h-10, rounded-lg, --green-dim bg, text-lg
- **Card titles:** font-semibold, sm:text-base, --text color, group-hover: green
- **Card descriptions:** text-xs, leading-relaxed, --muted color

**Cards present:**
1. 📊 Equity Calculator (`/equity`)
2. 🎓 Study (`/study`)
3. 🎯 Practice (`/practice`)
4. 🔍 Analyze (`/analyze`)
5. 🏆 ICM Calculator (`/icm`)
6. 📚 Courses (`/courses`)
7. � Push/Fold Charts (`/push-fold`)
8. � Range Explorer (`/range-explorer`)
9. ♠ Strategy Explorer (`/strategy`)
10. 🎲 Spots Database (`/spots`)
11. 🃏 Game Variants (`/variants`)
12. 📝 Hand History (`/hand-history`)

### Stats Section (below cards)
- **Layout:** grid-cols-2 md:grid-cols-4, gap-6, with border-top (--border)
- **Stat items:** centered text, number in green (2xl-3xl font-extrabold), label in --muted
- **Stats:** "1M+ Hands Analyzed", "10K+ Active Users", "500+ GTO Solutions", "50+ Training Modules"

### Footer tagline
- "Built for serious poker players. Data-driven. GTO-optimized." - --muted, centered

---

## Page 2: Study Preflop - `/study/preflop`

### Visual State
- **Average color:** White (#F1F1F1) - BRIGHT white page content area
- **Bg above nav:** Dark #111111 (same as all pages)
- **Content area:** Pure white/light background
- **Layout:** Main content area in white/light theme (unlike dashboard which is dark)
- Same sticky nav bar as homepage

---

## Page 3: Study Postflop - `/study/postflop`

### Visual State
- **Average color:** White (#F1F1F1) - BRIGHT white page content area (identical to study-preflop)
- Same structure and layout as study-preflop
- White content area with dark header/nav
- Screenshot file size identical to study-preflop (46603 bytes) - possibly same template or redirect

---

## Page 4: Practice/Trainer - `/practice`

### Visual State
- **Average brightness:** 18.7/255 - DARK theme
- **Content area:** Very dark (rgb(14,14,14) in middle)
- **Sidebar area (at x=290):** Shows a slightly lighter background rgb(28,28,30) - likely a sidebar or secondary background
- **Green accent markers at left edge:**
  - y=300: green (#00C853)
  - y=400: green
  - y=500: green
  - y=550: dark green fading (rgb(0,48,20))
- These green markers on the far-left suggest active sidebar navigation items / a vertical indicator bar

---

## Page 5: Equity - `/equity`

### Visual State
- **Average brightness:** 30.3/255 - DARK theme
- **Left edge scan shows:**
  - y=150: rgb(28,28,30) - content background
  - y=200: green accent (active state)
  - y=250: rgb(28,28,30)
  - y=300: green accent
  - y=350: rgb(94,94,96) - lighter element (text/card)
  - y=400: green accent
  - Multiple green vertical indicators visible
- **Middle area (nav bar area y=50):**
  - RGB values like (28,28,30) and (94,94,96) suggest cards/panels with slightly different backgrounds
- **Content area at y=860-920:** rgb(28,28,30) and (38,38,38) - panel/card backgrounds

---

## Page 6: ICM - `/icm`

### Visual State
- **Average brightness:** 15.7/255 - VERY DARK theme (darkest page)
- **Left edge scan:**
  - y=200: rgb(230,230,230) - very light element (text/heading on dark bg)
  - y=250: rgb(102,102,102) - gray text/card
  - y=800: rgb(102,102,102)
  - Most other areas: rgb(14,14,14) - extremely dark
- **Middle area:** Mostly uniform dark rgb(14,14,14) with occasional gray elements (135,135,135 at y=880)
- Very minimal content visible before interaction

---

## Page 7: Courses - `/courses`

### Visual State
- **Average brightness:** 18.5 - DARK theme
- **Left edge scan=200,250: rgb(230,230,230) - light text headings
  - y=700: rgb(48,24,23) - warm tint (unusual reddish)
  - y=800: rgb(230,230,230) - light element
  - y=850: rgb(39,39,39)
- **Middle area:** Uniform dark rgb(14,14,14) throughout (consistent dark content area)

---

## Page 8: Solutions/Analyze - `/analyze`

### Visual State
- **Average brightness:** 25.7/255 - DARK theme (slightly lighter than others)
- **Left edge scan:**
  - y=200: rgb(230,230,230) - light heading
  - y=300: rgb(102,102,106) - gray text
- **Middle area (y=860-920):**
  - Starts with green (#00C853) at far left
  - rgb(28,28,30) backgrounds
  - Various gray elements: rgb(142,142,147), rgb(124,124,128) - card/panel backgrounds
  - rgb(230,230,230) at some positions - white text/elements
- Has more visible content structure than other dark pages

---

## Summary of Key Visual Patterns

| Aspect | Value |
|--------|-------|
| Primary accent color | `#00C853` (vivid green) |
| Background (dashboard/homepage) | `#0E0E0E` - near black |
| Content pages background | Mixed: white (study), dark (practice/equity/icm/courses/analyze) |
| Nav bar | `#111111` with `#1A1A1A` border, 52px height |
| Nav pill bg | `#0A0A0A` with `#1D1D1D` border |
| Text colors | --text (white), --muted (#9A9A9A), --green (#00C853) |
| Card backgrounds | `--panel` (~#1a1a1a) or white depending on page theme |
| Font family | Inter (Google Fonts) |
| Active nav indicator | Green vertical bar at far left edge (~x=2736) |
| Logo | 28x28px green rounded square with "W" |
| CTA button | Green (#00C853) with black text, rounded-xl, font-weight 600 |
| Green "NEW" badges | background:#00C853, color:#000, 10px font, 4px radius |
| Responsive container | mx-auto px-4, content for sm/md/lg/xl |

### Navigation Items (in order, center nav)
1. Hold'em (`/equity`)
2. PLO (`/equity/plo`)
3. Stud (`/equity/stud`)
4. Razz (`/equity/razz`)
5. Badugi (`/equity/badugi`)
6. Play (`/play`)
7. 🎓 Study (`/study`)
8. 📈 Push/Fold [NEW] (`/push-fold`)
9. � Range [NEW] (`/range-explorer`)
10. � Practice (`/practice`)
11. 🔍 Analyze (`/analyze`)

### Notes
- The actual GTO Wizard site (GTOWizard.com) has a different layout with a left sidebar navigation
- This clone uses a **top horizontal navigation bar without a sidebar** on desktop
- The green accent at the far right of the nav bar (x=2657-2850) is likely the active state indicator or upgrade button area
- The study pages appear to use a white/light theme while other pages use dark theme
- The dashboard feature cards use a `hover: -translate-y-0.5` interaction pattern
