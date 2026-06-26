#!/usr/bin/env python3
"""
image_to_3d_classical.py — Instant CPU 3D reconstruction without any ML model.

Pipeline: classical depth heuristics -> normals -> point cloud -> Delaunay mesh -> trimesh -> GLB.
Runs in ~1s with zero downloads. Quality is lower than neural approach.

Requirements:
  pip install numpy scipy Pillow trimesh

Usage:
  python3 image_to_3d_classical.py path/to/image.png [--output output.glb] [--res 256]
"""

import argparse, os, sys, time, warnings
import numpy as np
import trimesh
from PIL import Image
from scipy import ndimage
from scipy.spatial import Delaunay

warnings.filterwarnings("ignore")


def estimate_depth_classical(img_gray):
    """Depth from dark channel prior + texture gradients + edges + vertical position."""
    h, w = img_gray.shape
    dark = ndimage.minimum_filter(img_gray, size=15)
    local_mean = ndimage.uniform_filter(img_gray, size=7)
    texture = np.sqrt(np.clip(
        ndimage.uniform_filter(img_gray**2, size=7) - local_mean**2, 0, None
    ))
    texture = texture / (texture.max() + 1e-8)
    edges = np.abs(ndimage.sobel(img_gray, 0)) + np.abs(ndimage.sobel(img_gray, 1))
    edges = ndimage.gaussian_filter(edges, 3)
    edges = edges / (edges.max() + 1e-8)
    vertical = np.broadcast_to(np.linspace(0, 1, h).reshape(-1, 1), (h, w)).copy()
    depth = 0.25*(1-dark) + 0.30*texture + 0.15*edges + 0.30*vertical
    depth = ndimage.gaussian_filter(depth, 4)
    depth = (depth - depth.min()) / (depth.max() - depth.min() + 1e-8)
    return depth.astype(np.float32)


def compute_normals(depth, scale=2.0):
    dzdx, dzdy = ndimage.sobel(depth, 1), ndimage.sobel(depth, 0)
    n = np.stack([-dzdx*scale, -dzdy*scale, np.ones_like(depth)], axis=-1)
    return (n / (np.linalg.norm(n, axis=-1, keepdims=True) + 1e-8)).astype(np.float32)


def generate_point_cloud(depth, rgb, normals, fov=60.0, max_pts=80000):
    h, w = depth.shape
    f = w / (2*np.tan(np.radians(fov)/2))
    cx, cy = w/2.0, h/2.0
    u, v = np.meshgrid(np.arange(w), np.arange(h))
    z = depth * 3.0
    x, y = (u-cx)*z/f, -(v-cy)*z/f
    pts = np.stack([x.ravel(), y.ravel(), z.ravel()], -1)
    cols = rgb.reshape(-1, 3)
    norms = normals.reshape(-1, 3)
    valid = z.ravel() > 0.02
    pts, cols, norms = pts[valid], cols[valid], norms[valid]
    if len(pts) > max_pts:
        idx = np.random.RandomState(42).choice(len(pts), max_pts, replace=False)
        idx.sort()
        pts, cols, norms = pts[idx], cols[idx], norms[idx]
    return pts, cols, norms


def reconstruct_mesh(points, colors):
    u = (points[:,0]-points[:,0].min())/(points[:,0].max()-points[:,0].min()+1e-8)
    v = (points[:,1]-points[:,1].min())/(points[:,1].max()-points[:,1].min()+1e-8)
    faces = Delaunay(np.stack([u,v],-1)).simplices
    v0,v1 = faces[:,1]-faces[:,0], faces[:,2]-faces[:,0]
    areas = np.linalg.norm(np.cross(
        points[faces[:,1]]-points[faces[:,0]],
        points[faces[:,2]]-points[faces[:,0]]
    ), -1)
    mask = areas < (np.mean(areas)+3*np.std(areas))
    return points, faces[mask], colors


def build_mesh(verts, faces, colors):
    m = trimesh.Trimesh(vertices=verts, faces=faces,
        vertex_colors=(colors*255).astype(np.uint8), process=True)
    m.update_faces(m.nondegenerate_faces())
    m.remove_unreferenced_vertices()
    return m


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("image")
    parser.add_argument("--output", "-o", default=None)
    parser.add_argument("--resolution", "-r", type=int, default=256)
    parser.add_argument("--fov", type=float, default=60.0)
    parser.add_argument("--max-points", type=int, default=80000)
    args = parser.parse_args()
    output = args.output or os.path.splitext(args.image)[0]+"_3d_classical.glb"
    print(f"Image -> 3D (classical, CPU, no ML)\n  {args.image} -> {output}\n")
    t0 = time.time()
    img = Image.open(args.image).convert("RGB").resize(
        (args.resolution, args.resolution), Image.BICUBIC)
    rgb = np.array(img, dtype=np.float32)/255.0
    gray = rgb.mean(2).astype(np.float32)
    print("[1] Depth estimation (classical)...")
    depth = estimate_depth_classical(gray)
    print("[2] Normals...")
    normals = compute_normals(depth)
    print("[3] Point cloud + mesh...")
    pts, cols, norms = generate_point_cloud(depth, rgb, normals, args.fov, args.max_points)
    verts, faces, vcols = reconstruct_mesh(pts, cols)
    mesh = build_mesh(verts, faces, vcols)
    print(f"  {len(mesh.vertices)}v / {len(mesh.faces)}f")
    mesh.export(output)
    print(f"\nDone in {time.time()-t0:.1f}s -> {output}")

if __name__ == "__main__":
    main()
