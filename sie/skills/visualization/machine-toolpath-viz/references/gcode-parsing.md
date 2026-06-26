# G-code Parsing Reference

Quick reference for parsing G-code into structured toolpath data for visualization.

## Move types

| Command | Type | Meaning |
|---------|------|---------|
| `G0` | Rapid travel | Moves at max speed, no material deposited |
| `G1` | Linear interpolation | Controlled move, may extrude or just position |

A G1 move is an **extrusion** (printing move) when its `E` parameter is non-zero (typically `abs(E) > 0.001`). Everything else is a travel move.

## Parameter letters

| Letter | Meaning | Units |
|--------|---------|-------|
| `X` | X coordinate | mm |
| `Y` | Y coordinate | mm |
| `Z` | Z coordinate (layer height) | mm |
| `E` | Extrusion amount | mm of filament |
| `F` | Feed rate | mm/min |
| `I`, `J` | Arc center offsets | mm |
| `S` | Spindle speed / temperature | varies |

## Comment handling

G-code supports **two comment styles**:

1. **Inline comments** — start with `;` and run to end of line:
   ```gcode
   G1 Z2.50 F3000 ; lift nozzle
   ```
   Always strip `;` and everything after before parsing coordinates.

2. **Block delete** — lines starting with `/` are skipped by default in most controllers. These are rare in slicer output.

## Parsing example — robust approach

```python
import re

LINE_PAT = re.compile(r'^(G[01])\s+(.*)')
AXIS_LETTERS = set('XYZEF')

def parse_gcode(path):
    moves = []
    current_z = 0.0
    
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(';'):
                continue
            
            m = LINE_PAT.match(line)
            if not m:
                continue
            
            cmd = m.group(1)
            # Strip inline comment before parsing params
            rest = m.group(2).split(';')[0].strip()
            
            params = {}
            for token in rest.split():
                if len(token) >= 2 and token[0] in AXIS_LETTERS:
                    try:
                        params[token[0]] = float(token[1:])
                    except ValueError:
                        pass  # skip malformed values
            
            x, y, z, e = params.get('X'), params.get('Y'), params.get('Z'), params.get('E')
            
            if x is not None and y is not None:
                moves.append({
                    'cmd': cmd,
                    'x': x, 'y': y,
                    'z': current_z,
                    'e': e if e is not None else 0.0,
                    'extrude': cmd == 'G1' and e is not None and abs(e) > 0.001,
                })
            
            if z is not None:
                current_z = z
    
    return moves
```

## Edge cases encountered

### 1. Non-standard words after `;` removal

Some G-code contains tokens that look like parameters but aren't:

```gcode
G1 Z2.50 F3000 ; lift nozzle
```

After stripping `; lift nozzle`, the remaining `F3000` has `F` as its key letter with value `3000`. This is fine if you include `F` in your AXIS_LETTERS set, but `lift` would crash `float('lift')`. The `AXIS_LETTERS` filter prevents this.

**Lesson**: Only parse parameters for known axis letters (`XYZEF`), not every token that starts with a letter.

### 2. Positive-only vs bidirectional E

Different slicers emit E differently:
- Some use ever-increasing E (cumulative filament)
- Others reset E to 0 at each layer or feature
- A few emit positive E for extruding and negative E for retraction

**Pattern**: Check `abs(e) > 0.001` rather than `e > 0` to filter out tiny floating-point artifacts from actual retractions.

### 3. Multiple G1 moves with same Z

A single physical layer typically contains many G-code lines — the outer perimeter, inner perimeters, and infill all at the same Z height. Group moves by `round(z, 1)` or `round(z, 2)` to get per-layer segments.

### 4. G92 (set position)

Some G-code files use `G92 E0` to reset the extruder position. This doesn't affect visualization but means E values can't be naively summed across the whole file.

## Coordinate space mapping

When converting G-code to Three.js (or any 3D graphics library):

| G-code axis | Three.js axis | Notes |
|-------------|---------------|-------|
| X | X | Horizontal (often build plate width) |
| Y | Z | Horizontal (often build plate depth) |
| Z | Y | Vertical (build height) — Three.js uses Y as up |

So a G-code point `(X=3000, Y=200, Z=5)` becomes `(x=3000, y=5, z=200)` in Three.js space.
