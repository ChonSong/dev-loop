---
name: compas-bim-to-print
description: Use compas + compas_slicer for BIM-to-G-code pipeline with openings (doors/windows). Build meshes, boolean subtract openings via CGAL, slice, print-organize, export G-code.
---

# compas BIM-to-Print Pipeline

Use for: taking wall/column profiles with openings → G-code for concrete 3D printing.

## Dependencies

```
compas>=2.15
compas-slicer @ git+https://github.com/compas-dev/compas_slicer.git@v0.8.0
```

## Pipeline Steps

```python
from compas.datastructures import Mesh
from compas.geometry import Box, Frame, Point, Vector, boolean_difference_mesh_mesh
from compas_slicer.slicers import PlanarSlicer
from compas_slicer.print_organization import PlanarPrintOrganizer
from compas_slicer.print_organization.print_organization_utilities.gcode import create_gcode_text
from compas_slicer.config import GcodeConfig
```

1. **Build mesh** — create Box for each wall/column, subtract opening boxes via `boolean_difference_mesh_mesh`
2. **Union** — combine all elements with `boolean_union_mesh_mesh`
3. **Slice** — `PlanarSlicer(mesh, layer_height=10.0).slice_model()`
4. **Organize** — `PlanarPrintOrganizer(slicer).create_printpoints()`
5. **G-code** — `create_gcode_text(organizer, GcodeConfig())`

## Key API

- `Mesh.from_shape(Box(...))` then `.quads_to_triangles()`
- `boolean_difference_mesh_mesh((V,F), (V,F))` returns `(V,F)` tuple
- `PlanarSlicer.mesh` must be triangular (use quilts before calling)
- Paths: `slicer.layers[i].paths[j]` — `.points`, `.is_closed`
- First closed path = outer contour, subsequent = holes

## Visualization

Use Three.js `ShapeGeometry` with `shape.holes` array for filled-polygon rendering, not line strips. See `examples/compas_viz.py`.

## Pitfalls

- compas_slicer v0.8.0 requires compas>=2.15 — install from GitHub, not PyPI
- `boolean_difference_mesh_mesh` returns a single `(V,F)` tuple (combined), not a list
- Mesh must be triangular (triangulate with `.quads_to_triangles()`)
- `GcodeConfig` is a TOML-backed dataclass — set attributes, not constructor kwargs
- G-code writer creates FDM-style output (retraction, purge line, fan) — concrete printers need modified config
