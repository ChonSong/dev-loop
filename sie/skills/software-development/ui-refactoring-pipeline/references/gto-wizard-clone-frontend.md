# GTO Wizard Clone — Frontend Stack Reference

**Project:** GTO Wizard Clone — open-source poker training platform
**Repo:** `gto-wizard-clone` under `/home/sc/repos/` on the host
**Live at:** wiz.codeovertcp.com (port 3000, Cloudflare tunnel + Access)

## Stack

| Layer | Technology |
|-------|-----------|
| Framework | Next.js 15 (App Router) |
| UI Library | React 19 |
| Styling | Tailwind CSS 4 (`@tailwindcss/postcss`) |
| Icons | lucide-react |
| Utilities | class-variance-authority, clsx |
| E2E Tests | Playwright |
| Backend | Python FastAPI (port 8000) |

## Key Source Locations (within `apps/web/`)

```
src/
├── app/
│   ├── equity/page.tsx          # NLH equity calculator (748 lines, has mock data)
│   ├── plo/page.tsx             # PLO equity
│   ├── icm/page.tsx             # ICM calculator
│   ├── bomb-pot/page.tsx        # Bomb Pot variant
│   ├── double-board/page.tsx    # Double Board variant
│   ├── omaha/page.tsx           # Omaha variant
│   ├── layout.tsx               # Root layout
│   └── page.tsx                 # Home/landing
├── components/
│   ├── equity/
│   │   ├── EquityHeatmap.tsx    # 169-hand grid heatmap
│   │   ├── EquityChart.tsx      # Bar chart comparison
│   │   ├── EquityBar.tsx        # Horizontal equity bar
│   │   ├── RangeGrid.tsx        # Hand range selector
│   │   └── RangeSelector.tsx    # Range input component
│   ├── hh/                      # Hand history viewer
│   ├── icm/                     # ICM calculator widgets
│   ├── strategy/                # Strategy matrices
│   ├── train/                   # Quiz/training components
│   └── Header.tsx               # Navigation (inline styles, custom)
```

## Existing Routes

| Route | Page | Status |
|-------|------|--------|
| `/equity` | Hold'em equity | ✅ Exists (mock data) |
| `/plo` | PLO equity | ✅ Exists |
| `/play` | Play mode | ✅ |
| `/study` | Study content | ✅ |
| `/practice` | Practice/quiz | ✅ |
| `/train` | Training | ✅ |
| `/analyze` | Hand analysis | ✅ |
| `/icm` | ICM calculator | ✅ |
| `/bomb-pot` | Bomb Pot variant | ✅ |
| `/double-board` | Double Board | ✅ |
| `/omaha` | Omaha variant | ✅ |
| `/spots` | Strategy spots | ✅ |
| `/strategies` | Saved strategies | ✅ |
| `/courses` | Course content | ✅ |

## Routing Style

All pages use App Router convention: `src/app/<route>/page.tsx`.
Most are `'use client'` pages with hooks.

## API Backend

FastAPI running on port 8000, routes under `/api/v1/`.
Example: equity calc → `POST /api/v1/equity/calculate`

## Variant Registry (back-end, recently added)

10 variants registered via pokerkit:
- NLH, PLO4, PLO5, Omaha8, Stud, Stud8, Razz, 2-7 TD, 2-7 SD, Badugi

Routes at `/api/v1/variants/` — list, info, equity calculation per variant.
Frontend pages for stud/draw variants still need to be built.

## Navigation Convention

Header uses custom inline styles (not Tailwind utility classes) — dark theme (`#111111` background, green accent `#00C853`).
Current nav tabs: Hold'em, PLO, Play, Study, Practice, Analyze.
