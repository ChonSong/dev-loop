# GTO Wizard Exact Design Tokens

Extracted from 50+ real GTO Wizard screenshots via vision_analyze analysis.
Screenshots stored at `/workspace/gto-wizard-references/`.

## Color Palette

| Token | Hex | Usage |
|-------|-----|-------|
| `--gto-bg` | `#1a1a1a` | Page background |
| `--gto-bg-elevated` | `#2a2a2a` | Card surfaces, sidebar |
| `--gto-bg-card` | `#333333` | Inner card surfaces, dropdowns |
| `--gto-bg-hover` | `#3a3a3a` | Hover state |
| `--gto-bg-input` | `#444444` | Input backgrounds |
| `--gto-bg-input-border` | `#555555` | Input borders |
| `--gto-bg-table-alt` | `#33333350` | Alternating table rows |
| `--gto-accent` | `#00C9A7` | Primary buttons, active tabs, indicators |
| `--gto-accent-hover` | `#00b898` | Button hover |
| `--gto-accent-dim` | `#00C9A720` | Active tab backgrounds |
| `--gto-text-primary` | `#ffffff` | Headings, primary text |
| `--gto-text-secondary` | `#aaaaaa` | Body text |
| `--gto-text-tertiary` | `#888888` | Labels, metadata |
| `--gto-text-muted` | `#555555` | Disabled text |
| `--gto-border` | `#3a3a3a` | Card borders, dividers |
| `--gto-border-light` | `#444444` | Input borders |
| `--gto-border-faint` | `#2a2a2a` | Subtle dividers |
| `--gto-red` | `#FF3B30` | Bets, raises, negative EV |
| `--gto-green` | `#34C759` | Calls, positive EV, checks |
| `--gto-blue` | `#30B0C7` | Folds, low equity |
| `--gto-orange` | `#FF9F0A` | Medium equity, diamonds |
| `--gto-purple` | `#AF52DE` | Rare actions |
| `--gto-pink` | `#FF2D55` | All-in |
| `--gto-matrix-selected` | `#FF9F0A` | Hand is in range (orange) |
| `--gto-matrix-excluded` | `#2a2a2a` | Hand not in range |

## Typography

| Element | Size | Weight | Color |
|---------|------|--------|-------|
| Nav tabs (STUDY/PRACTICE) | 13px | 500 | white / #888 |
| Page heading (h1) | 16px | 700 | white |
| Section headers | 12px | 600 | #888 uppercase |
| Body text | 13px | 400 | #888 |
| Labels (form) | 11px | 600 | #888 uppercase |
| Table data | 13px | 400 | white/gray |
| Matrix cells | 14px | 700 | white/#666 |
| Score display | 32px | 700 | varies |
| Small metadata | 10px | 500 | #555 |
| Button text | 13px | 600 | white |
| Font family | Inter/system | — | font-sans |
| Monospace | JetBrains Mono | — | font-mono (values) |

## Spacing & Dimensions

| Element | Size |
|---------|------|
| Matrix cell | 46×46px (or 48×48px) |
| Matrix gap | 2px |
| Sidebar icon bar | 30px width |
| Main content max | 1600px |
| Card padding | 20px (p-5) |
| Grid gap | 12px (gap-3) |
| Section gap | 16px (space-y-4) |
| Header height | 48px (h-12) |

## Input Styling

```
bg-[#444] border border-[#555] rounded-md px-3 py-2.5 text-white font-mono text-[13px]
focus:outline-none focus:border-[#00C9A7] transition-colors
```

## Button Styling

**Primary:** `px-5 py-2 bg-[#00C9A7] hover:bg-[#00b898] disabled:opacity-50 text-white rounded-md font-semibold text-[13px] shadow-lg shadow-[#00C9A7]/20`

**Secondary:** `px-4 py-2 bg-[#333] hover:bg-[#444] disabled:opacity-50 text-[#888] rounded-md text-[13px] border border-[#444]`

**Segment toggle:** `flex bg-[#2a2a2a] rounded-md p-0.5` with active `bg-[#00C9A7] text-white`

## Card Styling

```
bg-[#2a2a2a] border border-[#3a3a3a] rounded-xl p-5
```

Inner card: `bg-[#333] rounded-lg p-4`

## Error Message Styling

```
bg-[#FF3B30]/20 border border-[#FF3B30]/40 text-[#FF6B60] rounded-lg px-4 py-3 text-[13px]
```

## Nav Structure

```
┌─────────────────────────────────────────────────────┐
│ 🧙 GTO Wizard  STUDY  PRACTICE  ANALYZE   ⬆️ ? ⚙️ 👤 │
├────┬────────────────────────────────────────────────┤
│ 📊 │ Main Content Area                              │
│ 🎓 │                                                 │
│ 📜 │ 14 sub-pages under /gto/{equity,solver,...}    │
└────┴─────────────────────────────────────────────────┘
```

Icon sidebar (30px): Study/Practice/Analyze toggle icons
Main sidebar (280px): Context-sensitive items for active tab

## Nav Tab Colors

- **Active tab**: White text + 2px `#00C9A7` underline
- **Inactive tab**: `#888` text, no underline
- **Active sidebar item**: `#00C9A7` text on `#00C9A7/15` bg
- **Inactive sidebar item**: `#888` text hover→white on `#2a2a2a` bg

## App Header

Height: 48px (h-12)
Border-bottom: 1px solid `#2a2a2a`
Logo: 🧙 + "GTO Wizard" gradient (from `#00C9A7` to emerald-300)
Right side: Upload button (bg-[#2a2a2a]), help/settings icons, profile avatar

## Matrix Hierarchical Structure

```
         A    K    Q    J    T    9    8    7    6    5    4    3    2
    A    AA   AKs  AQs  AJs  ATs  A9s  A8s  A7s  A6s  A5s  A4s  A3s  A2s
    K    AKo  KK   KQs  KJs  KTs  K9s  K8s  K7s  K6s  K5s  K4s  K3s  K2s
    Q    AQo  KQo  QQ   QJs  QTs  Q9s  Q8s  Q7s  Q6s  Q5s  Q4s  Q3s  Q2s
    ...
    (Pairs on diagonal, suited top-right, offsuit bottom-left)
```

## Equity Bar Colors (Win/Tie/Loss)

- **Loss** (0-33%): `#FF3B30` (red), intensity scales with win %
- **Low** (33-45%): `#FF9F0A` (orange)
- **Even** (45-55%): `#aaaaaa` (gray)
- **Good** (55-67%): `#30B0C7` (blue)
- **Strong** (67-100%): `#34C759` (green)

## Action Color Coding

| Action | Color | Hex |
|--------|-------|-----|
| Fold | Gray/Blue | `#30B0C7` |
| Check | Gray | `#888888` |
| Call | Green | `#34C759` |
| Bet | Red | `#FF3B30` |
| Raise | Red | `#FF3B30` |
| All-in | Pink | `#FF2D55` |

## Reference Screenshots

`/workspace/gto-wizard-references/` contains 50+ images organized by area:

### Equity / Range Matrix
- `equity_matrix_13x13.jpg` — Main range matrix with stats panel below
- `range_builder_header.jpg` — Range builder UI
- `range_overlay_matrix.jpg` — Range overlay on 13x13 matrix
- `range_selector_options.jpg` — Range selection panel
- `range_equity_bars.jpg` — Equity bar visualization

### Strategy / Solver
- `strategy_full_view.jpg` — Full solver output with strategy list
- `strategy_grid_view.jpg` — Action frequency grid
- `strategy_ev_comparison.jpg` — Side-by-side EV comparison
- `strategy_board_texture.jpg` — Board texture analysis
- `strategy_bet_sizing.jpg` — Bet sizing strategy
- `solver_results_explained.png` — Solver results
- `solver_config_custom.png` — Solver configuration

### Breakdown / Analysis
- `breakdown_tab_overview.jpg` — Equity distribution chart
- `breakdown_tab_ev_chart.jpg` — EV chart
- `breakdown_tab_equity_distribution.jpg` — Equity distribution
- `breakdown_tab_range_detail.jpg` — Range detail breakdown

### Training
- `training_tips_overview.png` — Training interface
- `training_premade_drills.jpg` — Pre-made drills

### Hand History
- `hand_history_analyzer_thumbnail.jpg` — Hand history table
- `hand_history_upload_thumbnail.jpg` — Upload screen

### Aggregate Reports
- `aggregate_reports_overview.jpg` — Reports dashboard
- `aggregate_reports_heatmap.jpg` — Position heatmap
- `aggregate_reports_spider.jpg` — Spider chart
- `aggregate_reports_loss_areas.jpg` — Loss areas

### Analyze Mode
- `analyze_mode_elite_overview.png` — Analyze dashboard
- `analyze_mode_hands_pepe_emote_tiers.png` — Hand analysis

## How to Use References for UI Replication

1. Use `delegate_task` with `web` and `terminal` toolsets to find and download screenshots
2. Use `vision_analyze` on each screenshot to extract pixel-level design details
3. Compare multiple screenshots of the same element for consistency
4. Extract exact color hex values, font sizes, spacing, and layout structure
5. Create a design token file (like `styles/gto-tokens.ts`) with all extracted values
6. Build components referencing the token system rather than hardcoding values
