---
name: machine-toolpath-viz
description: "Parse machine coordinate data (G-code, CNC, 3D-printing toolpaths) and render interactive 3D layer-by-layer visualizations in the browser using Three.js"
version: 1.0.0
author: Hermes
tags: [visualization, 3d, threejs, gcode, manufacturing, toolpath]
related_skills: [interactive-knowledge-graph]
---

# Machine Toolpath Visualization

Parse coordinate-based manufacturing data (G-code toolpaths) and render them as interactive 3D visualizations. Covers G-code parsing, coordinate extraction, layer grouping, Three.js scene construction, layer-by-layer animation controls, and headless verification.

## When to use

- User has generated G-code (from a slicer, CAM tool, or custom pipeline) and wants to see it visually
- User asks "can we render the end result" from a manufacturing/CNC/3D-printing pipeline
- Visualizing CNC paths, robot trajectories, extruder toolpaths, or any layered coordinate data
- Debugging toolpath issues — verify layer order, travel moves, print/nozzle paths before physical print

## How to use

### 1. Parse G-code into move data

Write a Python script that reads G-code and extracts X, Y, Z, E (extrusion) values per move:

```python
import re

def parse_gcode(path):
    """Parse G-code file into structured move records."""
    moves = []
    current_z = 0.0
    line_pat = re.compile(r'^(G[01])\s+(.*)')
    
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(';'):
                continue
            m = line_pat.match(line)
            if not m:
                continue
            
            cmd = m.group(1)
            # Split off inline comments and parse params
            rest = m.group(2).split(';')[0].strip()
            params = {}
            for part in rest.split():
                if len(part) >= 2 and part[0] in 'XYZEF':
                    try:
                        params[part[0]] = float(part[1:])
                    except ValueError:
                        pass
            
            x, y, z, e = params.get('X'), params.get('Y'), params.get('Z'), params.get('E')
            if x is not None and y is not None:
                moves.append({
                    'cmd': cmd,
                    'x': x, 'y': y, 'z': current_z,
                    'e': e if e is not None else 0.0,
                    'extrude': cmd == 'G1' and e is not None and abs(e) > 0.001,
                })
            if z is not None:
                current_z = z
    
    return moves
```

Key parsing pitfalls (see `references/gcode-parsing.md` for details):
- Strip inline comments (`;`) before parsing parameters
- Some G-code lines contain non-standard words (e.g. "lift", "F6000") — filter param keys to known axes only (`XYZEF`)
- G0 = rapid travel (non-printing move), G1 = controlled print/extrude move
- E values > 0.001 indicate active extrusion (the nozzle is printing)
- Multiple moves can share the same Z — group by rounded Z value for layer separation

### 2. Group moves by layer

```python
def group_by_layer(moves):
    layers = {}
    for m in moves:
        z_key = round(m['z'], 2)
        if z_key not in layers:
            layers[z_key] = []
        layers[z_key].append(m)
    return layers
```

### 3. Generate Three.js standalone HTML

Build a self-contained HTML page that loads Three.js from CDN (via importmap) and renders the toolpath.

Key design choices:

**Scene setup:**
- Dark background (`#0d1117`) with ambient + directional lighting
- Grid helper for spatial reference (spacing relative to model scale)
- OrbitControls for user interaction (rotate, pan, zoom)
- Camera positioned above and to the side of the build plate

**Layer rendering:**
- Each Z layer gets a `THREE.Line` with its own `BufferGeometry`
- Color per layer (cycle through a palette of 5-10 distinct colors)
- Start all layers invisible, reveal progressively
- Current layer: full opacity; previous layers: 0.3 opacity for context
- Travel moves (G0 without E) can be omitted from the line geometry — they just clutter the view

**Controls:**
- Play button: animate through layers sequentially (50-100ms per layer)
- Reset button: return camera to initial position, show first layer
- Scroll/mousewheel: step through layers manually when not playing
- OrbitControls: drag to rotate, right-click to pan

**Performance for large files:**
- Cap points per layer (e.g. `pts.slice(0, 200)`) for files with >100k moves
- Sample every Nth layer if there are many layers (e.g. every 48th of 960)
- Each layer's geometry flattens point pairs into a position array: `[x1, z1, y1, x2, z2, y2, ...]`
- Use `Float32BufferAttribute` for efficient GPU memory

### 4. Self-contained HTML structure

```html
<script type="importmap">
{
  "imports": {
    "three": "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js",
    "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"
  }
}
</script>

<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
// ... scene setup, layer rendering, animation controls
</script>
```

### 5. Serving and verifying

```bash
# Serve for browser access
cd examples/ && python3 -m http.server 9090

# Then open http://localhost:9090/toolpath_viz.html
# Or tunnel behind Cloudflare for remote access
```

## References

- `references/gcode-parsing.md` — G-code format, move types, comment handling, edge cases

## Common pitfalls

- **G-code inline comments**: Semicolons (`;`) start comments. Always strip them before parsing coordinate parameters. The word after a semicolon (e.g. "lift") is not a valid float.
- **Non-coordinate words**: G-code files may include non-axis words like `F6000` (feed rate) or `E0.0` (extrusion). Filter parameter keys to `XY Z E F` only — or just `XYZEF` — and wrap `float()` in try/except.
- **E value polarity**: Some slicers output positive E for extrusion, others interleave positive and negative. Filter by `abs(e) > 0.001` rather than `e > 0`.
- **Multiple moves at same Z**: A single layer often contains many G-code lines. Group by rounded Z value, not expecting Z-change markers.
- **Z = 0**: The first print layer may be at Z = nozzle_offset (e.g. Z=2.5mm), not 0. The grid should appear at Y=0 in Three.js space.
- **Coordinate scale**: G-code is usually in mm. Ensure the camera distance and grid size match the model scale. A 3m wall needs a much larger grid (4000mm) than a 100mm column.
- **Browser performance**: For files with >100k moves and >500 layers, cap the rendered data. Sample every Nth layer and cap points per layer to keep the scene responsive.
- **Y and Z axis mapping**: In G-code, Z is vertical (build plate height). In Three.js, Y is vertical by convention. Map G-code (X, Y, Z) to Three.js (X, Z, Y) so Z-up becomes Y-up.
