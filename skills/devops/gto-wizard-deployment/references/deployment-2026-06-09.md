# GTO Wizard Deployment — Session Reference (2026-06-09)

## Deployment State (Live at wiz.codeovertcp.com)

| Service | Port | Path | Status |
|---------|------|------|--------|
| Frontend (Next.js 15) | 8564 | `~/gto-wizard-clone/apps/web` | Production build (20 pages) |
| API (FastAPI) | 8003 | `~/gto-wizard-clone` (PYTHONPATH: apps/api:packages/poker-core/src) | 96 routes, healthy |
| DB (SQLite) | — | `~/gto_wizard.db` | 60 quiz spots, 3 courses, 18 strategies |
| Tunnel | — | `~/.cloudflared/gto-wizard-real-config.yml` | Tunnel ID: 24362d8c-acda-43ca-87d7-9f422b631b11 |
| Domain DNS | — | CNAME → `24362d8c-acda-43ca-87d7-9f422b631b11.cfargotunnel.com` | Proxied (orange cloud) |

## Tunnel Config (Active)
```yaml
tunnel: 24362d8c-acda-43ca-87d7-9f422b631b11
credentials-file: /home/hermeswebui/.cloudflared/gto-wizard-original-creds.json
no-autoupdate: true
ingress:
  - hostname: wiz.codeovertcp.com
    service: http://localhost:8564
  - service: http_status:404
```

API is NOT in the tunnel ingress. Instead, it's proxied through Next.js rewrites in `next.config.ts`:
```typescript
async rewrites() {
  return [
    { source: '/api/:path*', destination: 'http://localhost:8003/api/:path*' },
    { source: '/icm/:path*', destination: 'http://localhost:8003/icm/:path*' },
    { source: '/plo4/:path*', destination: 'http://localhost:8003/plo4/:path*' },
    { source: '/double-board/:path*', destination: 'http://localhost:8003/double-board/:path*' },
    { source: '/bomb-pot/:path*', destination: 'http://localhost:8003/bomb-pot/:path*' },
    { source: '/ws/:path*', destination: 'http://localhost:8003/ws/:path*' },
  ]
}
```

## Frontend Overhaul (2026-06-09)

### What Changed
- **globals.css** — replaced Tailwind-heavy theme with reference CSS variables (`--bg: #0E0E0E`, `--green-bright: #7CFC7C`, etc.)
- **Header.tsx** — full replacement with premium nav (Hold'em/PLO/Play/🎓Study/Practice/Analyze pills, Upgrade button, icon buttons, avatar)
- **Layout.tsx** — removed footer, added Inter font (Google Fonts), updated themeColor to `#0E0E0E`
- **New `/study` page** — faithful React conversion of study_page.html with 13×13 hand matrix, action cards, position bar, hand combo detail
- **Homepage** — redirects to `/study`

### Key Files
| File | Lines | Purpose |
|------|-------|---------|
| `src/app/globals.css` | ~50 | CSS variables from reference |
| `src/app/layout.tsx` | ~70 | Layout + Inter font + SW init |
| `src/components/Header.tsx` | ~150 | Premium nav with all tabs |
| `src/app/study/page.tsx` | ~400 | Study page (matrix, actions, combos) |
| `src/app/page.tsx` | ~5 | Redirect to /study |

### Verification Commands
```bash
# Check title
curl -sL https://wiz.codeovertcp.com/ | grep '<title>'

# Check all services
curl -s https://wiz.codeovertcp.com/api/v1/health
curl -s https://wiz.codeovertcp.com/api/v1/quiz/random | python3 -m json.tool
curl -s https://wiz.codeovertcp.com/api/v1/courses

# Check study page content
curl -sL https://wiz.codeovertcp.com/study | grep -o 'Take action|Cash 100bb|Allin 100|Hands'
```

## Dual-Base Fix (2026-06-09)

**Problem:** SQLAlchemy `Base` in `services/database.py` (DeclarativeBase) and `services/models.py` (declarative_base) were different instances. Models registered with one Base were invisible to the other.

**Fix:**
1. `database.py`: Changed `class Base(DeclarativeBase)` → `class Base(DeclarativeBase, AsyncAttrs)` — added AsyncAttrs mixin
2. `services/models.py`: Removed `Base = declarative_base(cls=AsyncAttrs)` — now imports from `database.py`
3. `models/spots.py` already imported from `services/models.py` — transitively picks up unified Base
4. Re-deleted `~/gto_wizard.db` and re-ran `PYTHONPATH=apps/api:packages/poker-core/src python3 seed_all.py`

**After fix:** Quiz spots return real random spots (`curl /api/v1/quiz/random`), courses return 3 items, strategies still 0 (PostgreSQL-only storage).
