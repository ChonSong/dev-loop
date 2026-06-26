# Export Implementation Patterns

## Files Created (2026-07)

| File | Purpose |
|------|---------|
| `apps/web/src/lib/exportUtils.ts` | Core export functions — `renderGridToPNG`, `renderBarChartToPNG`, `renderEquityChartToPNG`, `downloadBlob`, `downloadFromApi`, `timestampedFilename` |
| `apps/web/src/components/ui/ExportButton.tsx` | Reusable export button component with dropdown menu |
| `apps/web/src/components/hh/LeakChartWithExport.tsx` | Wrapper adding export to LeakChart |

## Files Modified

| File | Change |
|------|--------|
| `apps/api/routers/hh.py` | Fixed JSONB column serialization in CSV export (stakes, winners, players, board) |
| `apps/web/src/app/strategies/page.tsx` | Full rewrite with ExportButton (PNG + CSV) on strategy heatmap |
| `apps/web/src/app/equity/page.tsx` | Added ExportButton to Equity Line Chart (PNG via SVG→Canvas, CSV) |
| `apps/web/src/app/analyze/hands/page.tsx` | Connected CSV export to backend `GET /api/v1/hh/export` with client-side fallback |
| `apps/web/src/app/analyze/leaks/page.tsx` | Switched to `LeakChartWithExport` |
| `apps/web/src/components/equity/EquityHeatmap.tsx` | Added optional `onExport` prop |

## Key Technical Decisions

1. **No html2canvas dependency** — All PNG exports use Canvas API directly to avoid adding ~200KB dependency
2. **Grid rendering** — `renderGridToPNG` draws cells with `ctx.fillRect` + `ctx.strokeRect` + `ctx.fillText`, supporting custom colors, opacity (frequency), and text labels
3. **SVG→PNG for recharts** — Extract SVG element by ID, serialize with `XMLSerializer`, load into `Image`, draw to canvas at 2x scale, export via `canvas.toBlob`
4. **Backend CSV** — Uses FastAPI `StreamingResponse` with `Content-Disposition` header; frontend reads `Content-Disposition` for filename, falls back to `timestampedFilename()` if header missing
5. **ExportButton pattern** — Single option = direct click; multiple options = dropdown. Always shows loading state during async export.

## Canvas Grid Rendering Parameters

```typescript
// Strategy heatmap defaults
renderGridToPNG(grid, filename, {
  cellSize: 36,
  padding: 16,
  headerSize: 28,
  title: "GTO Strategy — Kd7h2c BTN 100bb",
  titleColor: '#d4af37',
  labelColor: '#9ca3af',
  backgroundColor: '#030712',
  scale: 2,
});

// Bar chart defaults
renderBarChartToPNG(data, filename, {
  width: 640,
  height: 360,
  title: "Leak Analysis",
  scale: 2,
});
```

## Action Color Mapping (Strategy Heatmap)

| Category | Color | Actions |
|----------|-------|---------|
| Bet/Raise | `#3b82f6` (blue) | bet, raise, push, allin |
| Check/Call | `#22c55e` (green) | check, call |
| Fold | `#ef4444` (red) | fold |

Cell opacity = `Math.max(0.15, frequency)` — higher frequency = more opaque.
