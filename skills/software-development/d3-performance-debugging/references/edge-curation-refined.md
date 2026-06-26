# Skill Graph Edge Curation — Refined Taxonomy (June 2025)

## Problem

Original graph had all 75 nodes appearing **disconnected** despite 2775 same-category pairs — because all skills had `category: "uncategorized"` (cardinality=1). Pure category/tag edges are only useful when categories have high cardinality.

## Edge Type Taxonomy (Refined)

| Edge Type | Construction | Default | Safe Limit |
|---|---|---|---|
| `member-of` | All pairs in same namespace | **OFF** | ~40 edges per namespace; disable for ns with 10+ members |
| `workflow-peer` | Nodes sharing same `workflow_role` | **ON** | All-to-all within role groups (~507 edges max) |
| `quality-hub` | Top 20% (q ≥ 7) fully connected | **ON** | 21 nodes → ~210 edges max |
| `tool-use` | Nodes sharing tool names | OFF | Sparse/Noisy; cap at 100 |
| `cross-ref` | Explicit cross-ns references | OFF | Only if data has them |

**Total curated for 75 nodes: ~500 edges** — readable at default settings.

## Quality Score Formula

```
q  = 2.0  if verified
   + 1.5  if has_examples
   + 1.0  if has_pitfalls_defined
   + 0.5  if has_testing_guidance
   + 0.5  if has_crossrefs
   + 1.0  if version not in ('', '1.0.0')
   + min(2.0, code_examples / 5)
   + min(1.5, pitfalls_count / 6)
   + min(1.0, step_count / 20)
```
Node size = `6 + q * 1.8`. q=7 → size~18.6. q=0 → size~6.

## Filter Toggle Behavior (in HTML)

Active edge types stored in `Set`. On toggle button click:
```js
activeTypes.has(type) ? activeTypes.delete(type) : activeTypes.add(type);
rebuildGraph();
```
`rebuildGraph()` calls `graph.graphData({nodes, links: filteredEdges})` — no full re-init needed.

Default active at load: `workflow-peer` + `quality-hub` only.
Default OFF: `member-of` (too dense for large ns) + `tool-use` (noisy).

## Lessons

- **Default state IS architecture**: A checkbox default ON creates the failure mode. member-of ON for creative (19 nodes) = 171 same-category pairs alone.
- **Quality hub at q≥7 threshold** creates a tight, high-signal cluster of top-developed skills without connecting everyone.
- **300–600 edges for 75 nodes is readable**. 1000+ needs filtering. 2000+ is unreadable.
- **CORS on JSON fetch**: Always inline GRAPH_DATA directly in the HTML — never fetch external JSON.
- **Duplicate edges**: Sort src/tgt alphabetically per edge before deduplication with a seen set.
- **Node verdical ring**: Draw in `nodeCanvasObject` after layer for verified nodes — `ctx.beginPath(); ctx.arc(..., node.size+2.5, 0, 2*Math.PI)`.
