# 3D Reconstruction from 2D Images — Technology Landscape (2025)

## State of the Art: LRM Architecture

The dominant approach is the **Large Reconstruction Model (LRM)** — a feed-forward transformer that takes a single RGB image and directly outputs a 3D mesh.

### Ancestry
```
LRM (Hong et al. 2023) — foundational paper
  └── TripoSR (Tripo AI / Stability AI, Mar 2024)
        └── Stable Fast 3D (Stability AI, Aug 2024) — UV unwrapping + PBR materials
              └── SPAR3D (Stability AI, Jan 2025) — point cloud conditioning for backside quality
  └── InstantMesh (Tencent ARC, Apr 2024) — multi-view diffusion + LRM hybrid
```

### How LRM Works
1. **Input**: Single RGB image (256x256 or 512x512)
2. **Image Encoder**: ViT extracts multi-scale features
3. **Triplane Decoder**: Features decoded into 3 orthogonal 2D feature planes (XY, XZ, YZ)
4. **MLP Query**: Sample triplane per 3D point, predict SDF/occupancy
5. **Marching Cubes**: SDF grid to mesh (via torchmcubes)
6. **Texture Baking**: Vertex colors or UV textures

### Top Repos (GPU-required)

| Repo | Stars | License | VRAM | Speed | Output |
|------|-------|---------|------|-------|--------|
| TripoSR | 6590 | MIT | 6GB | 0.5s | Textured mesh |
| InstantMesh | 4412 | Apache 2.0 | 8GB | Fast | Textured mesh |
| Stable Fast 3D | — | NC | 10GB | Fast | UV+PBR mesh |
| SPAR3D | 1045 | NC | 7-10.5GB | Fast | Point cloud + mesh |

## CPU-Only Pipeline (No GPU Required)

When no CUDA GPU is available, use this pipeline. Lower quality than LRM but runs entirely on CPU.

### Architecture
```
Image -> DPT-Hybrid-MiDaS depth estimation (CPU, 30-120s)
      -> Normal estimation (Sobel gradients)
      -> Point cloud (perspective projection)
      -> 2D Delaunay triangulation (scipy)
      -> Mesh cleanup (trimesh)
      -> Export (GLB/OBJ/PLY with vertex colors)
```

### Dependencies
```bash
# CRITICAL: Use CPU index to avoid 2GB CUDA download
/app/venv/bin/pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
/app/venv/bin/pip install transformers Pillow numpy scipy trimesh
```

**PITFALL**: In the Hermes WebUI Docker container, always use `/app/venv/bin/pip` explicitly.
Bare `pip install` may target a different Python and packages won't be found at runtime.

**PITFALL**: `torchvision` must be installed separately from `torch`. The transformers
depth estimation pipeline fails with "AutoImageProcessor requires torchvision" if missing.

### Model Download
DPT-Hybrid-MiDaS (~345MB) downloads on first use from HuggingFace, cached at ~/.cache/huggingface/.
```python
from transformers import pipeline
pipe = pipeline("depth-estimation", model="Intel/dpt-hybrid-midas", device=-1)
```

### Performance (Intel i3-6100U, 8GB RAM, no GPU)
| Resolution | Depth | Mesh | Total | Output |
|------------|-------|------|-------|--------|
| 256x256 | ~30s | ~1s | ~31s | ~2MB GLB |
| 512x320 | ~60s | ~1s | ~61s | ~2MB GLB |
| 512x512 | ~120s | ~2s | ~122s | ~5MB GLB |

### Quality Notes
- **Good for**: Single clear objects centered in frame (products, furniture, statues)
- **Limitations**: Backside geometry interpolated from depth gradients, not real. No occlusion handling.
- **Not for**: Transparent/reflective surfaces (noisy depth), complex multi-object scenes

### Alternative: Classical Depth (No Download)
Dark channel prior + texture gradients + edge density + vertical position heuristics.
Quality worse but runs in ~1s with zero downloads. See scripts/image_to_3d.py.

## Headless Docker Pitfall: Open3D

**Open3D requires X11/GL shared libraries** (libX11.so.6, libGL.so.1). It fails in headless
Docker containers with: `OSError: libX11.so.6: cannot open shared object file`.

**Workaround**: Use `trimesh` + `scipy.spatial.Delaunay` for mesh operations instead.
Trimesh is pure Python with numpy/scipy deps and works in any container.

## Quick Decision Guide

```
Has CUDA GPU?
+-- YES -> TripoSR (MIT, fastest) or SPAR3D (best quality)
+-- NO
    +-- Can wait 2 min + download 345MB?
    |   +-- YES -> DPT depth -> point cloud -> Delaunay mesh
    +-- Need instant?
        +-- Classical heuristic depth -> point cloud -> Delaunay mesh
```

## Cloud APIs (when local isn't feasible)
- Tripo AI: api.tripo3d.ai (free tier)
- Replicate: camenduru/instantmesh (pay per run)
- HuggingFace Spaces: stabilityai/TripoSR, TencentARC/InstantMesh
- Meshy API: image to 3D
