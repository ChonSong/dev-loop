# Viewport Overflow from CSS Grid `aspectRatio: 1/1'`

## Problem

A CSS grid with `aspectRatio: '1/1'` on each cell creates square cells that scale with the container width. For a 13×13 grid in a ~750px wide container, each cell is ~40px × 40px, making the grid ~520px tall. Combined with page headers, navigation, and interactive elements below the grid, the total page height exceeds the viewport.

**Symptom:** Elements exist in the DOM and are functional but `getBoundingClientRect().bottom > window.innerHeight`. Users can't see or interact with elements without scrolling.

## Fix Pattern

Replace `aspectRatio: '1/1'` with fixed `height` and use flex layout:

```tsx
// Page container:
<div style={{ height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
  <div style={{ flexShrink: 0 }}>header</div>
  <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '...', minHeight: 0 }}>
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: 0 }}>
      <div style={{ flex: 1, overflow: 'auto' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(13, 1fr)' }}>
          {cells.map(cell => (
            <div style={{ height: 22, fontSize: 9 }}>{cell}</div>
          ))}
        </div>
      </div>
    </div>
    <div>action buttons here</div>
  </div>
</div>
```

## Key Principles

1. `height: 100vh` + `flexDirection: column` prevents overflow
2. `flexShrink: 0` on fixed headers
3. `flex: 1` + `overflow: auto` on scrollable areas
4. `minHeight: 0` on flex children with grids
5. Fixed `height` for cells, not `aspectRatio: '1/1'`
6. Verify with `getBoundingClientRect()` — critical elements must be within `window.innerHeight`
