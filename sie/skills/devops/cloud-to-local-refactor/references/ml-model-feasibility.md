# ML Model Feasibility Assessment

Pattern for determining whether a GPU-dependent ML model can run on a given machine. Triggered by "can I run X locally?" or "is Y feasible on my hardware?" questions.

## Diagnostic Sequence

```bash
# 1. GPU check
nvidia-smi                    # If this fails → no NVIDIA GPU
nvidia-smi --query-gpu=memory.total --format=csv,noheader  # VRAM in MB

# 2. CPU / RAM
cat /proc/cpuinfo | grep "model name" | head -1
nproc                         # Thread count
cat /proc/meminfo | grep MemTotal  # KB → divide by 1M for GB

# 3. Disk space for model weights
df -h /workspace

# 4. CUDA availability in PyTorch
python3 -c "import torch; print(torch.cuda.is_available())"
```

## Common VRAM Requirements (Feed-Forward 3D Models)

| Model | VRAM | RAM | GPU Required | Notes |
|-------|------|-----|-------------|-------|
| TripoSR | ~6GB | 8GB | Yes (CUDA) | MIT license, easiest entry |
| Stable Fast 3D | ~8-10GB | 16GB | Yes (CUDA) | UV-unwrapped + PBR |
| SPAR3D | ~10.5GB (7GB low-vram) | 16GB | Yes (CUDA) | Gated HF model |
| InstantMesh | ~8GB | 16GB | Yes (CUDA) | Multi-view diffusion + LRM |

## CPU-Only Fallbacks

When no GPU is available, feed-forward transformer models are **not viable** (100x slower, often OOM). Alternatives:

- **MiDaS depth estimation** → depth map → point cloud (runs on CPU, ~300MB model)
- **Cloud API**: Tripo AI, Meshy, Replicate.com (pay-per-run)
- **Check host machine**: `ssh host nvidia-smi` — if host has GPU, run there instead

## Key Heuristics

- If `nvidia-smi` fails → model won't run locally unless CPU fallback exists
- If VRAM < model requirement → won't fit even with batch size 1
- If RAM < 2× model size → will likely OOM during loading
- CPU-only inference of transformer models: expect 5-10 min per image vs <1s on GPU
- Always state the limitation honestly — don't suggest "try it and see" for obvious mismatches
