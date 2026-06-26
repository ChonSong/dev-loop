# Screenshot rendering tells

Heuristics for determining whether a headless Chrome screenshot captured real rendered content vs a blank/skeleton page.

## File size heuristics

For a 1920x1080 PNG of a dark-themed dashboard/knowledge-graph page:

| File size | What it means |
|-----------|---------------|
| <30 KB | Likely blank/skeleton. Only background color rendered, no content. |
| 30-100 KB | Partial content — maybe header + legend but graph canvas didn't render |
| 100-400 KB | Reasonable — some visual content but possibly missing heavy canvas elements |
| 400-600 KB | Fully rendered graph with nodes, edges, labels |
| >600 KB | Dense graph with many visible elements |

Compare against a known-good screenshot from the same page for reference.

## Common failure modes and their tells

| Failure | Screenshot symptom | File size pattern |
|---------|-------------------|-------------------|
| JS syntax error | Only static HTML (header text, legend) renders | Small (~20-25KB) |
| CDN script failed to load | Page loaded but no graph canvas | Small (~25-50KB) |
| Force sim still running when screenshot taken | Partial layout, nodes still moving/clustered | Medium (100-200KB) |
| `--virtual-time-budget` not set | Graph canvas didn't render yet | Small (~57KB observed) |
| Chrome 143 `--screenshot` bug (no IDAT) | PNG file exists but cannot be decoded | Exactly ~21KB regardless of content |
| Page fully rendered | Graph visible with distinct node clusters and edge lines | Large (400-500KB+) |

## Validation test

If unsure whether the screenshot shows real content:

```python
import struct

def is_valid_png(path):
    with open(path, 'rb') as f:
        d = f.read()
    if d[:8] != b'\x89PNG\r\n\x1a\n':
        return False
    pos = 8
    while pos < len(d):
        l = struct.unpack('>I', d[pos:pos+4])[0]
        ct = d[pos+4:pos+8]
        if ct == b'IDAT':
            return True  # Has actual pixel data
        pos += 12 + l + 4
    return False  # Header only, no pixel data (Chrome 143 bug)
```

If the PNG validates but the file size suggests rendering failure, use the `debug-live-website` skill's delegation or file-size heuristic fallback.
