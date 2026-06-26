# Agent-OS Frontend Migration & Theme System

## Theme System (Phase 3a — May 2026)

### Architecture
- `src/context/ThemeContext.tsx` — React context provider with 11 themes
- `src/main.tsx` — wraps `<App />` with `<ThemeProvider>`
- `src/index.css` — theme CSS variables under `[data-theme='xxx']` selectors
- `src/pages/SettingsPage.tsx` — `ThemePicker` component at top of settings page

### Available Themes
| Theme | Label | Dark | Accent |
|-------|-------|------|--------|
| `bento` | Warm Bento | No | `#FAD4C0` (peach) |
| `matrix` | Matrix | Yes | `#00ff41` (green) |
| `matrix-light` | Matrix Light | No | `#008f2d` |
| `claude-official` | Claude Official | Yes | `#6366f1` (indigo) |
| `claude-official-light` | Claude Light | No | `#2557b7` |
| `claude-classic` | Claude Classic | Yes | `#b98a44` (gold) |
| `claude-classic-light` | Classic Light | No | `#b98a44` |
| `claude-slate` | Claude Slate | Yes | `#7eb8f6` (blue) |
| `claude-slate-light` | Slate Light | No | `#3b82f6` |
| `claude-nous` | Nous Dark | Yes | `#ffac02` (amber) |
| `claude-nous-light` | Nous Light | No | `#2557b7` |

### CSS Utility Classes
Components should use theme-aware classes instead of hardcoded colors:
- `.theme-bg` — `background-color: var(--theme-bg)`
- `.theme-panel` — `background-color: var(--theme-panel)`
- `.theme-card` — `background-color: var(--theme-card)`
- `.theme-border` — `border-color: var(--theme-border)`
- `.theme-text` — `color: var(--theme-text)`
- `.theme-muted` — `color: var(--theme-muted)`
- `.theme-accent-bg` / `.theme-accent-text` — accent colors

### Adding a New Theme
1. Add entry to `src/context/ThemeContext.tsx` THEMES array
2. Add `[data-theme='name']` CSS block to `src/index.css` with all variables:
   `--theme-bg`, `--theme-sidebar`, `--theme-panel`, `--theme-card`, `--theme-card2`,
   `--theme-border`, `--theme-border-subtle`, `--theme-text`, `--theme-muted`,
   `--theme-accent`, `--theme-accent-secondary`, `--theme-accent-subtle`, `--theme-accent-border`, `--theme-focus`

## Repo-Transmute Frontend Migration (Phase 7 — May 2026)

### Tool Location
- GitHub: `github.com/ChonSong/repo-transmute` (branch: master)
- Host: `/opt/data/home/.hermes/hermes-sync/projects/repo-transmute/`

### Commands
```bash
cd /opt/data/home/.hermes/hermes-sync/projects/repo-transmute
PYTHONPATH=src python3 -m repo_transmute.cli frontend_blueprint <path>
PYTHONPATH=src python3 -m repo_transmute.cli theme_analysis <src> -t <tgt>
PYTHONPATH=src python3 -m repo_transmute.cli api_analysis <src> -t <tgt>
PYTHONPATH=src python3 -m repo_transmute.cli frontend_migrate <src> <tgt> --dry-run
```

### Modules
| File | Purpose | Lines |
|------|---------|-------|
| `frontend/component_extractor.py` | JSX/TSX component/route/API extraction | 497 |
| `frontend/css_mapper.py` | CSS variable/theme extraction + compatibility | 383 |
| `frontend/api_rewriter.py` | API call pattern detection + URL rewrite rules | 425 |
| `transpiler/validate.py` | React/TSX validation (tsc + vite build + syntax) | updated |
| `transpiler/prompts.py` | Frontend migration LLM prompts | updated |
| `transpiler/compatibility.py` | Frontend routing table + compatibility | updated |

### Test Results (hermes-workspace)
- 761 components extracted
- 22 themes (css-vars approach)
- 125 API call patterns
- 60% migration confidence (SSR + high component count penalty)

### Bug: UnboundLocalError in component_extractor.py
Fixed in `_extract_state()`: changed `if m:` to `if found_state:` since `m` is only defined inside the for loop. Pattern: always use a boolean flag when checking loop result outside the loop.
