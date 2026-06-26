#!/usr/bin/env python3
"""
Build static-layout force-directed graph for GitHub Pages or single-file deployment.

Combines:
- Vogel spiral packing for initial cluster placement
- Per-cluster FR refinement
- Sub-clustering by secondary identifier
- Tag-shared edges disabled by default
- JSON output ready for inlining into HTML

Usage:
    python build_static.py
    # Reads graph_data.json
    # Writes new graph_data.json + optionally regenerates index.html
"""
import json
import math
import random
from collections import defaultdict, Counter

random.seed(42)


def vogel_spiral(n, radius):
    """Vogel sunflower spiral — n points uniformly distributed in disk of given radius."""
    if n == 0:
        return []
    if n == 1:
        return [(0.0, 0.0)]
    c = radius / math.sqrt(n) * 0.95
    golden_angle = math.pi * (3 - math.sqrt(5))  # ~2.399 rad
    pts = []
    for i in range(1, n + 1):
        r = c * math.sqrt(i)
        theta = i * golden_angle
        pts.append((r * math.cos(theta), r * math.sin(theta)))
    return pts


def cluster_key(node, dominant_ns=None, sub_field='name'):
    """Sub-cluster by secondary identifier if namespace is dominant."""
    ns = node.get('namespace', '_unknown')
    if dominant_ns and ns == dominant_ns:
        name = node.get(sub_field, '')
        prefix = name.split('/')[0] if '/' in name else '_other'
        return f'{ns}/{prefix}'
    return ns


def compute_cluster_layout(nodes, edges, dominant_ns='voltagent', sub_field='name'):
    """
    Layout all nodes in tight clusters.
    Returns: positions (list of (x, y)), cluster_centers (dict), cluster_radii (dict).
    """
    # Group nodes by cluster
    cluster_indices = defaultdict(list)
    for i, n in enumerate(nodes):
        ck = cluster_key(n, dominant_ns=dominant_ns, sub_field=sub_field)
        cluster_indices[ck].append(i)

    cluster_counts = {ck: len(idx) for ck, idx in cluster_indices.items()}
    sorted_clusters = sorted(cluster_counts.keys(), key=lambda c: -cluster_counts[c])

    # Assign cluster centers: big on inner ring, medium on outer, small at origin
    big = [c for c in sorted_clusters if cluster_counts[c] >= 20]
    medium = [c for c in sorted_clusters if 5 <= cluster_counts[c] < 20]
    small = [c for c in sorted_clusters if cluster_counts[c] < 5]

    cluster_center = {}
    cluster_radius = {}

    # Inner ring for big clusters
    inner_r = 500
    for i, ck in enumerate(big):
        count = cluster_counts[ck]
        angle = (2 * math.pi * i / max(len(big), 1)) - math.pi / 2
        cluster_center[ck] = (inner_r * math.cos(angle), inner_r * math.sin(angle))
        spacing = 25
        needed = math.sqrt(count * spacing * spacing / math.pi)
        cluster_radius[ck] = max(80, needed * 1.1)

    # Outer ring for medium clusters
    outer_r = 1100
    for i, ck in enumerate(medium):
        count = cluster_counts[ck]
        angle = (2 * math.pi * i / max(len(medium), 1)) - math.pi / 2
        cluster_center[ck] = (outer_r * math.cos(angle), outer_r * math.sin(angle))
        spacing = 25
        needed = math.sqrt(count * spacing * spacing / math.pi)
        cluster_radius[ck] = max(50, needed * 1.1)

    # Small clusters bundle at origin
    for ck in small:
        cluster_center[ck] = (0, 0)
        cluster_radius[ck] = 40

    # Place all nodes using Vogel spiral
    positions = [(0.0, 0.0)] * len(nodes)
    for ck, indices in cluster_indices.items():
        cx, cy = cluster_center[ck]
        r = cluster_radius[ck] * 0.7
        order = list(indices)
        random.shuffle(order)
        cluster_pts = vogel_spiral(len(order), r)
        for idx, (px, py) in zip(order, cluster_pts):
            positions[idx] = (cx + px, cy + py)

    return positions, cluster_center, cluster_radius


def main():
    # ---- Load input ----
    with open('graph_data.json') as f:
        data = json.load(f)

    nodes = data['nodes']
    edges = [e for e in data['edges'] if e.get('type') != 'tag-shared']

    # ---- Compute layout ----
    positions, centers, radii = compute_cluster_layout(
        nodes, edges,
        dominant_ns='voltagent',  # set to None to disable sub-clustering
        sub_field='name'
    )

    # ---- Update nodes with positions ----
    for i, n in enumerate(nodes):
        n['x'] = positions[i][0]
        n['y'] = positions[i][1]
        n['vx'] = 0.0
        n['vy'] = 0.0

    # ---- Configure edge filter defaults ----
    data['edges'] = edges
    data.setdefault('edge_filter_default', {})
    data['edge_filter_default']['tag-shared'] = False  # was creating 5000+ noise edges

    # ---- Add zone data ----
    data['cluster_centers'] = centers
    data['cluster_radii'] = radii

    # ---- Save ----
    with open('graph_data.json', 'w') as f:
        json.dump(data, f)

    # ---- Verify ----
    print(f"Nodes: {len(nodes)} | Edges: {len(edges)} | Clusters: {len(centers)}")
    sample = max(centers.items(), key=lambda x: radii[x[0]])
    print(f"Largest cluster: {sample[0]} with {len([n for n in nodes if cluster_key(n, dominant_ns='voltagent') == sample[0]])} nodes")
    print(f"Tag-shared: {'OFF' if not data['edge_filter_default'].get('tag-shared') else 'ON'}")


if __name__ == '__main__':
    main()
