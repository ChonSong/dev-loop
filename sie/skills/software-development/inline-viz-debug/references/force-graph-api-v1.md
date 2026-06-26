# force-graph 1.x API Quirks (v1.43.5+)

## No `.linkOpacity()`

**Does not exist in v1.** The method was added in a later major version. Trying to call it throws a silent TypeError that kills the entire graph render.

### Control opacity instead via `linkColor`:

```js
function getLinkColor(link) {
  let base = link.color || '#555';
  if (opacity >= 0.99) return base;
  let r = parseInt(base.slice(1,3), 16) || 85;
  let g = parseInt(base.slice(3,5), 16) || 85;
  let b = parseInt(base.slice(5,7), 16) || 85;
  return `rgba(${r},${g},${b},${opacity})`;
}
```

### Trigger re-render on slider change:

```js
graph.linkColor(getLinkColor);  // NOT graph.linkOpacity()
```

### All available link methods in v1.43.5:

`linkColor`, `linkWidth`, `linkCurvature`, `linkDirectionalParticles`, `linkDirectionalArrowColor`, `linkDirectionalArrowLength`, `linkDirectionalArrowRelPos`, `linkDirectionalParticleColor`, `linkDirectionalParticleSpeed`, `linkDirectionalParticleWidth`, `linkHoverPrecision`, `linkLabel`, `linkLineDash`, `linkAutoColorBy`, `linkCanvasObject`, `linkCanvasObjectMode`, `linkPointerAreaPaint`, `linkSource`, `linkTarget`

## Node Methods

`.nodeColor()` — returns a color string. Use for both highlighting (search match gold ring, hover dimming) and base color.

## Initialization Pattern (static layout)

```js
graph = ForceGraph()(container)
  .graphData({ nodes, links })
  .nodeId('id')
  .nodeLabel(labelFn)
  .nodeVal(valFn)
  .nodeColor(colorFn)
  .linkColor(colorFn)
  .linkWidth(wFn)
  .linkCurvature(0.15)
  .backgroundColor('#0d0d14')
  .d3AlphaDecay(1)           // freeze sim immediately
  .d3VelocityDecay(1)
  .warmupTicks(0)
  .cooldownTicks(0)
  .onNodeClick(clickFn)
  .onBackgroundClick(() => hide())
  .onNodeHover(hoverFn)
  .onZoom(zoomFn)
  .nodeCanvasObjectMode(() => 'after')
  .nodeCanvasObject((node, ctx) => {
    // custom draw — e.g. verified checkmark ring, search highlight
  });
```
