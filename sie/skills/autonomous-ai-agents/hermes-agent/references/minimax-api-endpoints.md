# MiniMax API — Endpoint & Vision Troubleshooting

## Endpoint Discovery (May 2025)

**`api.minimax.chat` returns 401 Unauthorized.** The correct base URLs:

| Provider | Endpoint | API Mode |
|----------|----------|----------|
| MiniMax (international) | `https://api.minimax.io/anthropic` | `anthropic_messages` |
| MiniMax CN (China) | `https://api.minimaxi.com/anthropic` | `anthropic_messages` |

The `/anthropic` suffix is required — it triggers the `anthropic_messages` api_mode detection. Without it, calls return 401.

**Test command:**
```python
import urllib.request, json
key = os.getenv("MINIMAX_API_KEY")
payload = json.dumps({"model": "MiniMax-M2.7", "max_tokens": 5, "messages": [{"role": "user", "content": "hi"}]})
req = urllib.request.Request("https://api.minimax.io/anthropic/v1/messages", data=payload.encode(),
    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, method="POST")
with urllib.request.urlopen(req, timeout=15) as resp:
    print(json.loads(resp.read()))
```

## Vision Support

MiniMax-M2.7 supports vision but the content block format matters:

- **`image_url`** (OpenAI-style) → `400 Bad Request: unsupported content type 'image_url' (2013)`
- **`input_image`** (Anthropic-native) → works correctly

**Working vision payload:**
```python
{
    "model": "MiniMax-M2.7",
    "max_tokens": 50,
    "messages": [{
        "role": "user",
        "content": [
            {"type": "text", "text": "Describe this image."},
            {"type": "input_image", "image_url": "data:image/png;base64,..."}
        ]
    }]
}
```

Remote image URLs (http/https) also work in `input_image` blocks.

## Hermes Routing

In `agent/auxiliary_client.py`:

- `_PROVIDERS_WITHOUT_VISION` = `{"kimi-coding", "kimi-coding-cn"}` — minimax is NOT here, so minimax goes through main provider vision path
- `_ANTHROPIC_COMPAT_PROVIDERS` = `frozenset({"minimax", "minimax-oauth", "minimax-cn"})` — these use Anthropic-compatible wire format
- Vision auto-detect falls through: main provider → OpenRouter → Nous → stop

When `auxiliary.vision.provider: auto` and main provider is minimax, it uses minimax directly for vision (not an aggregator fallback) because minimax is not in `_PROVIDERS_WITHOUT_VISION`.

## Common Failure Modes

| Error | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` on `api.minimax.chat` | Wrong endpoint | Use `api.minimax.io/anthropic` |
| `400: unsupported content type 'image_url'` | Using OpenAI vision format | Switch to `input_image` (Anthropic format) |
| `400: unsupported content type 'input_image'` | Model doesn't support vision | Check model capabilities |
| Vision `400 Bad Request` with valid format | Image size/format issue | Try a smaller test image first |