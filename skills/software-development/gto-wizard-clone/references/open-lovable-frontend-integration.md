# Open Lovable Frontend Integration (Session Detail)

Created: 2026-06-06
Context: User corrected the frontend approach — "i thought we were going to use our modified open lovable"

## What Changed

The GTO Wizard Clone frontend was initially built as a custom Next.js app at `apps/web/` with a separate design system. The user's modified Open Lovable fork at `/workspace/open-lovable` became the canonical frontend framework.

## Files Modified

### `/workspace/open-lovable/next.config.ts`
Added API rewrites to proxy GTO backend requests:
```typescript
async rewrites() {
  return [
    { source: '/api/:path*', destination: 'http://localhost:8002/api/:path*' },
    { source: '/icm/:path*', destination: 'http://localhost:8002/icm/:path*' },
    { source: '/plo4/:path*', destination: 'http://localhost:8002/plo4/:path*' },
  ];
}
```
Key detail: hardcoded `localhost:8002` — not an env var. This works because backend always runs in the same container.

### `/workspace/open-lovable/tailwind.config.ts`
Added custom grid columns for the 13×13 hand matrix:
```typescript
extend: {
  gridTemplateColumns: { '13': 'repeat(13, minmax(0, 1fr))' },
  gridTemplateRows: { '13': 'repeat(13, minmax(0, 1fr))' },
}
```
Tailwind doesn't include grid-cols-13 by default — you MUST add it.

### `/workspace/open-lovable/app/gto/page.tsx` (NEW, 39KB)
Single-file client component containing all 4 tab panels:

| Tab | Component | API Calls |
|-----|-----------|-----------|
| Equity | `EquityCalculator` | `/api/v1/equity/calculate`, `/api/v1/equity/heatmap` |
| Solver | `SolverPanel` | `/api/v1/solver/solve`, `/api/v1/solver/status/{job_id}` (poll) |
| Strategy | `StrategyViewer` | `/api/v1/strategy/{key}` |
| ICM | `ICMCalculator` | `/icm/api/calculate` |

## Design Patterns Used

### Color palette (custom dark theme)
- Background: `#0a0a0f` (very dark)
- Cards: `bg-gray-800` (#1f2937) / `bg-gray-900` (#111827)
- Primary accent: `emerald-600` (#059669) with emerald-400 (#34d399) gradient for logo
- Range matrix: emerald-based coloring with equity-based opacity for heatmap
- Borders: `border-gray-800` / `border-gray-700/50`
- Text hierarchy: white (primary), gray-400 (secondary), gray-500 (tertiary)

### Quick range buttons
Inline bar with pre-defined ranges: AA, Top 5%, Top 10%, Top 20%, Any Pair, Broadways, All. Each maps to a comma-separated range string.

### Range builder modal
Full-screen overlay implementing:
- Fixed positioning: `fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm`
- 13×13 clickable hand matrix (toggle cells)
- Text input for range strings (AA,KK,AKs or AA+ or AA-TT)
- Quick range selects that update both the text input AND the temp set
- Selection counter: `tempRange.size` / `ALL_HANDS_LIST.length` hands
- Apply button writes formatted range to villainRange state

### 169-hand ordering for range display
The `ALL_HANDS_LIST` must follow poker convention: pairs first (AA→22), then suited (AKs→32s), then offsuit (AKo→32o). The `handName()` function computes the display string from row/col indices.

### Equity bar
```
<div className="w-full bg-gray-800 rounded-full h-6 overflow-hidden flex">
  <div className="h-full transition-all duration-300 flex items-center justify-center text-[11px] font-bold text-white"
    style={{ width: `${pct}%`, backgroundColor: equityColor(equity) }}>{pct}%</div>
</div>
```

### Equity heatmap grid
13×13 grid with `gap-px` and `bg-gray-900` container. Each cell shows the hand name and colors based on equity: `rgba(34, 197, 94, ${Math.max(0.1, eq)})`.

### Strategy action frequency bars
```
<div className="w-24 bg-gray-700 rounded-full h-2 overflow-hidden">
  <div className="h-full rounded-full" style={{ width: `${freq * 100}%`, backgroundColor: actionColor(action) }} />
</div>
```

## Open Lovable Component Structure

```
app/
  layout.tsx         → Root layout with Geist Sans/Mono + Inter + Roboto Mono fonts
  page.tsx           → AI builder landing page (HomePage, 891 lines)
  landing.tsx        → Landing page variant
  globals.css        → Imports styles/main.css
  gto/
    page.tsx         → GTO dashboard (new, 39KB)
  builder/
    page.tsx         → AI site builder (8.5KB)
  generation/
    page.tsx         → Code generation (180KB)
```

## Running

```bash
# 1. Start API backend (from gto-wizard-clone root)
cd /workspace/gto-wizard-clone
PYTHONPATH=/workspace/gto-wizard-clone/apps/api:/workspace/gto-wizard-clone \
  /app/venv/bin/uvicorn apps.api.main:app --host 0.0.0.0 --port 8002

# 2. Build + serve Open Lovable frontend
cd /workspace/open-lovable
export PATH="/home/hermeswebui/.hermes/home/.local/bin:$PATH"
./node_modules/.bin/next build
PORT=8555 ./node_modules/.bin/next start -p 8555

# 3. Verify
curl -s http://localhost:8555/gto | head -20
curl -s http://localhost:8555/api/v1/equity/health
```

## Zombie Port Detection

When port 8555 is held by a zombie next-server even after `kill -9`:
1. `cat /proc/net/tcp6 | grep -i "216B"` (8555 = 0x216B in hex)
2. Note the inode number from the output
3. `find /proc -maxdepth 2 -name "fd" -type d | while read d; do pid=$(echo $d | cut -d/ -f3); ls -l $d 2>/dev/null | grep -q "socket:\[INODE\]" && echo "PID=$pid" && kill -9 $pid; done`
4. `fuser -k` and `ss -tlnp` are NOT available in slim containers

## Build Verification

```bash
cd /workspace/open-lovable
export PATH="/home/hermeswebui/.hermes/home/.local/bin:$PATH"
./node_modules/.bin/next build
# Expected: ✓ Compiled successfully in ~54s, /gto page at ~13.7kB + 114kB shared
```
