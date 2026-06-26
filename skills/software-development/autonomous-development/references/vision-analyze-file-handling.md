# vision_analyze — File Path Handling

## Key Limitation

`vision_analyze` only accepts:
- HTTP/HTTPS URLs
- Files accessible from the **agent runtime** (not raw Python/execute_code context)

It does NOT accept `/tmp` paths from within `execute_code` or raw Python scripts in this container environment.

## Workarounds

### 1. Use delegate_task with vision toolset (RECOMMENDED)

Subagents with `toolsets: ["vision"]` can access local files directly:

```python
delegate_task(
    goal="Analyze /tmp/screenshot.png and describe functional elements",
    toolsets=["vision"]
)
```

### 2. Convert to data URL (may work for small images)

```python
import base64
with open('/tmp/image.png', 'rb') as f:
    b64 = base64.b64encode(f.read()).decode()
data_url = f"data:image/png;base64,{b64}"
# Then pass data_url to vision_analyze
```

Size limit: data URLs are encoded inline and consume context tokens rapidly. ~400KB PNG = ~540KB base64 string. Use only for thumbnails/small images.

### 3. Serve via HTTP (for large images)

If the host has a web server running, upload the image there and pass the URL.

## Verified Working Patterns

| Approach | Works? | Notes |
|----------|--------|-------|
| `vision_analyze("/tmp/file.png")` from agent context | YES | Agent runtime has file access |
| `vision_analyze("/tmp/file.png")` from execute_code | NO | Different runtime context |
| `vision_analyze("https://...")` | YES | HTTP URL always works |
| `vision_analyze("data:image/png;base64,...")` | MAYBE | Token-heavy, small images only |
| `delegate_task(goal, toolsets=["vision"])` | YES | Subagent has vision tool + file access |

## Session History

- Hyprland config screenshot (388KB) was successfully analyzed via `delegate_task` with vision toolset.
- execute_code could read the file but vision_analyze rejected the path.
- Converting to base64 data URL also failed (vision_analyze didn't process it in execute_code runtime).