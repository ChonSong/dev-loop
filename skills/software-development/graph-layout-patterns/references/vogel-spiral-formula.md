# Vogel's Sunflower Spiral — Reference

## The formula

For `n` points in a disk of radius `R`:

```
c = R / sqrt(n) * 0.95
for i in 1..n:
    r     = c * sqrt(i)
    theta = i * golden_angle         # golden_angle = π * (3 − sqrt(5)) ≈ 2.399 rad
    x     = r * cos(theta)
    y     = r * sin(theta)
```

The `0.95` factor prevents the outermost point (i=n) from overshooting `R`. The exact overshoot is `sqrt(n) * c / R - 1` which equals `(1/0.95) - 1 ≈ 5.3%` without the factor.

## Why this distribution is uniform

The sunflower / Vogel spiral is the *most uniform* non-lattice 2D point distribution known. Each new point lands in the largest remaining gap, which is exactly what the golden-angle winding does.

Properties:
- **No two points are very close** (min pairwise distance ≈ R * sqrt(π/n))
- **No large empty regions** (any disk of radius R/2 contains at least one point)
- **No preferred direction** (rotationally symmetric)

## Comparison to alternatives

| Method | Uniformity | Edge effects | Speed | Best for |
|---|---|---|---|---|
| Vogel spiral | Best (no lattice) | Smooth boundary | O(n) | ≤500 points |
| Hex grid | Excellent (lattice) | Hard edges | O(n) | ≤1000 points, need alignment |
| Poisson disk | Excellent | Hard | O(n²) | Need exact min-distance |
| Random | Poor | None | O(n) | Quick & dirty |
| Concentric rings | Good | Concentric | O(n) | Need radial structure |

## Visualization test

```python
import math
import random
random.seed(42)

def vogel(n, R):
    c = R / math.sqrt(n) * 0.95
    ga = math.pi * (3 - math.sqrt(5))
    return [(c*math.sqrt(i)*math.cos(i*ga), c*math.sqrt(i)*math.sin(i*ga))
            for i in range(1, n+1)]

# 200 points in radius 100
pts = vogel(200, 100)
# Check uniformity
import statistics
dists = [math.hypot(x, y) for x, y in pts]
print(f"max distance: {max(dists):.1f} (target: 95)")
print(f"min distance: {min(dists):.1f}")
# All points should be within ~95 of center
```

## Combined with charge repulsion (for >200 points)

Vogel works well up to ~500 points. Beyond that, inner points get crowded. For 1000+ points, use Vogel as initial placement then run a brief charge-repulsion pass (no attractive forces, no gravity, just a few iterations).

```python
def vogel_plus_charge(positions, iterations=20, k=15):
    """Vogel initial + charge repulsion refinement."""
    n = len(positions)
    pos = [list(p) for p in positions]
    vel = [[0, 0] for _ in range(n)]
    for it in range(iterations):
        for i in range(n):
            for j in range(i+1, n):
                dx, dy = pos[i][0]-pos[j][0], pos[i][1]-pos[j][1]
                d = math.hypot(dx, dy) + 0.01
                if d < k * 2:  # only push if too close
                    f = (k * k) / d
                    vel[i][0] += f*dx/d; vel[i][1] += f*dy/d
                    vel[j][0] -= f*dx/d; vel[j][1] -= f*dy/d
        cool = (k * 2) * (1 - it / iterations)
        for i in range(n):
            vx, vy = vel[i]
            s = math.hypot(vx, vy) + 0.01
            cap = min(s, cool)
            pos[i][0] += vx/s * cap
            pos[i][1] += vy/s * cap
            vel[i] = [0, 0]
    return pos
```

## Origin

Discovered by Hans Vogel in 1979 as a model for sunflower seed arrangements. The golden angle `137.5°` is the irrational limit that prevents points from aligning radially. Nature uses this exact pattern in sunflower heads, pine cones, and pineapples.
