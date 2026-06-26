---
name: bim-visualisation
description: Generate architectural-quality visualisations from BIM/floorplan data for 3D concrete printing. Three.js interactive viewer, Blender Cycles renders, plan/elevation views, QA assessment.
trigger: User asks to visualise a floor plan, generate architectural renders, create plan views, assess plan viability, or iterate on a building design.
---

# BIM visualisation — from floor plan to architectural renders

Three tiers of output, used for different purposes:

| Tier | Tool | When to use | What it produces |
|------|------|-------------|-----------------|
| Interactive 3D | Three.js BIM viewer | Design iteration, stakeholder review, section cuts | Web-based orbit/zoom/pan, orthographic plan/elevation views |
| Architectural renders | Blender Cycles via Docker | Presentation-quality images, compliance documentation | 6 standard views (perspective, plan, 4 elevations) at 1920px |
| Plan verification | QA assessment script | Engineering review, printability checks | Structural viability report, 20+ automated checks |

## Workflow

```
Floor plan JSON (GH-style profiles + openings)
    ↓
Step 1: QA assessment (scripts/qa_assess_plan.py)
    ↓
Step 2: IFC generation (scripts/generate_ifc.py)
    ↓
Step 3: G-code + SVG plan (bim2print CLI + gcode_to_svg.py)
    ↓
Step 4: Three.js viewer (docs/research/ifc_viewer.html)
    ↓
Step 5: Blender renders (scripts/blender_render.py)
    ↓
Deploy to tunnel + commit
```

## Three.js viewer

Located at `docs/research/ifc_viewer.html`. Key features:
- **View modes**: 3D perspective, Plan (orthographic top-down), N/S/E/W elevations
- **Section cuts**: Horizontal clipping plane slider with percentage indicator
- **Measurements**: Dimension overlays (wall length, width, thickness)
- **Materials**: Procedural concrete texture with noise + aggregate speckles
- **Lighting**: 3-point + hemisphere, shadow mapping, ACES filmic tone mapping
- **Interactions**: Orbit controls, hover highlighting, wireframe toggle

To add to the viewer:
1. Edit the `profiles` array in the HTML with your floor plan data
2. Each profile has: name, type, pts (polygon), z, h, mat, openings[]
3. Openings need: x, w, d (depth along wall face), z, h

## Blender pipeline

Runs headless via Docker (`nytimes/blender:latest`, Blender 3.3.1).

```bash
python scripts/blender_render.py --model examples/house_floorplan.json --output docs/research/renders --samples 32
```

Architecture:
- `scripts/blender_render.py` — CLI wrapper, reads JSON, generates inner script, runs Docker
- `scripts/_blender_render_inner.py` — actual Blender Python script executed inside container
- Injects floor plan data via string replacement (`__FLOORPLAN_JSON__`)
- Mounts `/output` for results

Renders 6 views: overview (3/4 perspective), plan (top-down, square), elevation-north/south/east/west.

**Pitfalls:**
- GLIBC 2.31 on host — ifcopenshell binary wheels won't load. Use pure-Python IFC generator instead (`scripts/generate_ifc.py`).
- Boolean modifiers in Blender fail silently on complex geometry. Use bmesh construction instead (wall polygon with openings, then extrude).
- First Blender render compiles Cycles kernels (~30s delay).
- Wall openings are cut using bmesh face deletions, not boolean modifiers — more reliable and faster.

## QA assessment

```bash
python scripts/qa_assess_plan.py examples/house_floorplan.json
```

Checks performed:
- Wall thickness (3DCP minimum: 150mm warn, 100mm fail)
- Wall height (printability range: 300-4000mm)
- Opening dimensions (height vs wall height, minimum opening size)
- Opening positions (sill height, structural weakness at Z=0)
- Polygon validity (minimum 3 points, no duplicates)
- Printability (layer count, total concrete volume)
- Structural enclosure (number of walls, footprint area)
- Door height clearance (minimum 2000mm)

## Design iteration loop

Cron job `bim2print-design-iteration` runs Mon/Thu 08:00:
```
QA → IFC → G-code → SVG plan → Blender render → commit + push
```

Or manually:
```bash
bash scripts/deploy_pipeline.sh examples/house_floorplan.json
```

## Floor plan format (GH-style JSON)

```json
[
  {
    "name": "Front-Wall",
    "ifc_type": "IfcWallStandardCase",
    "points_2d": [[x1,y1],[x2,y2],...],
    "base_elevation": 0.0,
    "height": 2400.0,
    "openings": [
      {
        "shape": [[x1,y1],[x2,y2],...],
        "z_start": 0.0, "z_end": 2100.0,
        "name": "Door-Name"
      }
    ]
  }
]
```

External walls: 200mm thick. Internal walls: 150mm minimum for 3DCP.
