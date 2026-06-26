#!/usr/bin/env python3
"""
image_to_3d_v2.py — CPU 3D reconstruction from a single image using neural depth estimation.

Pipeline: DPT-Hybrid-MiDaS depth (CPU) -> normals -> point cloud -> Delaunay mesh -> trimesh -> GLB.

Requirements:
  /app/venv/bin/pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
  /app/venv/bin/pip install transformers Pillow numpy scipy trimesh

Usage:
  /app/venv/bin/python3 image_to_3d_v2.py path/to/image.png [--output output.glb] [--res 512]

First run downloads ~345MB DPT model from HuggingFace.
"""

import argparse, os, sys, time, warnings
import numpy as np
import trimesh
from PIL import Image
from scipy import ndimage
from scipy.spatial import Delaunay

warnings.filterwarnings("ignore")


def load_image(path, max_res=512):
    img = Image.open(path).convert("RGB")
    ow, oh = img.size
    scale = min(max_res / ow, max_res / oh, 1.0)
    if scale < 1.0:
        img = img.resize((int(ow * scale), int(oh * scale)), Image.BICUBIC)
    arr = np.array(img, dtype=np.float32) / 255.0
    return arr, ow, oh


def estimate_depth(img_rgb):
    """DPT-Hybrid-MiDaS depth estimation on CPU."""
    print(f"  Loading DPT-Hybrid-MiDaS (first run: ~345MB download)...")
    t = time.time()
    from transformers import pipeline
    pipe = pipeline("depth-estimation", model="Intel/dpt-hybrid-midas", device=-1)
    img_pil = Image.fromarray((img_rgb * 255).astype(np.uint8))
    result = pipe(img_pil)
    depth = np.array(result["depth"], dtype=np.float32)
    depth = (depth - depth.min()) / (depth.max() - depth.min() + 1e-8)
    print(f"  Depth: {depth.shape} in {time.time()-t:.1f}s")
    return depth


def compute_normals(depth, scale=2.0):
    dzdx = ndimage.sobel(depth, axis=1)
    dzdy = ndimage.sobel(depth, axis=0)
    n = np.stack([-dzdx*scale, -dzdy*scale, np.ones_like(depth)], axis=-1)
    return (n / (np.linalg.norm(n, axis=-1, keepdims=True) + 1e-8)).astype(np.float32)


def generate_point_cloud(depth, img_rgb, normals, fov_deg=60.0, max_pts=100000):
    h, w = depth.shape
    f = w / (2.0 * np.tan(np.radians(fov_deg) / 2.0))
    cx, cy = w / 2.0, h / 2.0
    u, v = np.meshgrid(np.arange(w), np.arange(h))
    z = depth * 3.0
    x, y = (u - cx) * z / f, -(v - cy) * z / f
    pts = np.stack([x.ravel(), y.ravel(), z.ravel()], axis=-1)
    cols = img_rgb.reshape(-1, 3)
    norms = normals.reshape(-1, 3)
    valid = z.ravel() > 0.02
    pts, cols, norms = pts[valid], cols[valid], norms[valid]
    if len(pts) > max_pts:
        idx = np.random.RandomState(42).choice(len(pts), max_pts, replace=False)
        idx.sort()
        pts, cols, norms = pts[idx], cols[idx], norms[idx]
    return pts, cols, norms


def reconstruct_mesh(points, colors):
    u = (points[:, 0] - points[:, 0].min()) / (points[:, 0].max() - points[:, 0].min() + 1e-8)
    v = (points[:, 1] - points[:, 1].min()) / (points[:, 1].max() - points[:, 1].min() + 1e-8)
    faces = Delaunay(np.stack([u, v], axis=-1)).simplices
    verts = points
    v0, v1 = verts[faces[:,1]] - verts[faces[:,0]], verts[faces[:,2]] - verts[faces[:,0]]
    areas = np.linalg.norm(np.cross(v0, v1), axis=-1)
    mask = areas < (np.mean(areas) + 3 * np.std(areas))
    return verts, faces[mask], colors


def build_mesh(verts, faces, colors):
    mesh = trimesh.Trimesh(
        vertices=verts, faces=faces,
        vertex_colors=(colors*255).astype(np.uint8),
        process=True,
    )
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.remove_unreferenced_vertices()
    return mesh


def export_mesh(mesh, img_rgb, depth, output):
    h, w = img_rgb.shape[:2]
    x, y, z = mesh.vertices[:,0], mesh.vertices[:,1], mesh.vertices[:,2]
    f = w / (2*np.tan(np.radians(30)))
    u = np.clip((x*f/(z+1e-8)+w/2)/w, 0, 1)
    v = np.clip((-y*f/(z+1e-8)+h/2)/h, 0, 1)
    mesh.visual.uv = np.stack([u, v], axis=-1)
    ext = os.path.splitext(output)[1].lower()
    if ext not in (".glb", ".obj", ".ply", ".stl"):
        output += ".glb"
    mesh.export(output, file_type=ext.lstrip("."))
    print(f"  Saved: {output} ({os.path.getsize(output)/1e6:.1f}MB)")


def main():
    parser = argparse.ArgumentParser(description="Image to 3D (neural depth, CPU)")
    parser.add_argument("image")
    parser.add_argument("--output", "-o", default=None)
    parser.add_argument("--resolution", "-r", type=int, default=512)
    parser.add_argument("--fov", type=float, default=60.0)
    parser.add_argument("--max-points", type=int, default=100000)
    args = parser.parse_args()

    output = args.output or os.path.splitext(args.image)[0] + "_3d.glb"
    print(f"Image -> 3D (DPT, CPU)\n  {args.image} -> {output}\n")
    t_total = time.time()

    print("[1] Loading image...")
    img_arr, ow, oh = load_image(args.image, args.resolution)
    h, w = img_arr.shape[:2]
    print(f"  {w}x{h}")

    print("[2] Neural depth estimation (slow part)...")
    depth = estimate_depth(img_arr)

    print("[3] Computing normals...")
    normals = compute_normals(depth)

    print("[4] Reconstructing mesh...")
    pts, cols, norms = generate_point_cloud(depth, img_arr, normals, args.fov, args.max_points)
    print(f"  Points: {len(pts)}")
    verts, faces, vcols = reconstruct_mesh(pts, cols)
    mesh = build_mesh(verts, faces, vcols)
    print(f"  Mesh: {len(mesh.vertices)}v / {len(mesh.faces)}f")

    print("[5] Exporting...")
    export_mesh(mesh, img_arr, depth, output)

    print(f"\nDone in {time.time()-t_total:.1f}s -> {output}")


if __name__ == "__main__":
    main()
