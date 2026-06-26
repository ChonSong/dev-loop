# Fun-Audio-Chat Architecture & Integration Patterns

## Overview

Fun-Audio-Chat (`FunAudioLLM/Fun-Audio-Chat`) is a speech-to-speech model with its own WebSocket server. It is NOT a library you import and call as a Python function — it ships as a complete server with binary protocol.

## Key Architecture Facts

### Server (web_demo/server/server.py)
- **Framework**: `aiohttp` + `asyncio` for WebSocket
- **Endpoint**: `GET /api/chat` on port 11235 (default)
- **Protocol**: Binary messages with type byte:
  - `0x00` HANDSHAKE, `0x01` AUDIO, `0x02` TEXT, `0x03` CONTROL, `0x04` METADATA, `0x05` ERROR, `0x06` PING, `0x07` COLOREDTEXT
- **Control messages**: `0x00` START, `0x01` END_TURN, `0x02` PAUSE, `0x03` RESTART
- **Heartbeat**: 30s keepalive
- **Codec**: Opus via `sphn` library (24kHz WebSocket rate, 16kHz model rate)

### Inference Model
- **Model**: Qwen3 MoE-based, `torch.bfloat16`
- **Streaming**: Custom `FunaudioChatStreamer` that yields text tokens and audio tokens separately
- **Frame size**: 1920 samples @ 24kHz (80ms frames)
- **Parameters**: `token_hop_len=15`, `pre_lookahead_len=3`, `group_size=5`

### Concurrency Model
- **TTS Engine**: Runs in dedicated `multiprocessing.Process` to bypass Python GIL
- **GPU requirements**: 2 CUDA devices by default (cuda:0 for S2S model, cuda:1 for TTS)
- **Communication**: `asyncio.Queue`, `queue.Queue`, `mp.Queue` between async loops and threads
- **Start method**: Forces `spawn` to avoid CUDA context issues

### Interrupt Handling
- New `start` signal sets `current_generation['interrupt'] = True`
- Halts current generation and clears queues
- Maps to `context.cancel()` pattern in Python

### Key Dependencies
```
transformers==4.52.3
torch, torchaudio
sphn (Opus codec)
aiohttp (WebSocket server)
soundfile, librosa (audio processing)
onnxruntime-gpu (for some components)
tensorrt-cu12 (TensorRT acceleration)
```

## Integration Patterns

### Pattern 1: Local WebSocket Relay (Recommended)
Don't reimplement the server. Spawn it as a subprocess, connect to it via WebSocket, and bridge through your main multiplexer.

```go
// Go spawns Fun-Audio-Chat server
cmd := exec.Command("python", "server.py", "--port", "11235", "--model-path", "model/s2s")
cmd.Start()

// Go connects as WebSocket client
conn, _, _ := websocket.Dial(ctx, "ws://localhost:11235/api/chat")

// Bridge: client → Go → Fun-Audio-Chat server → Go → client
```

**Pros**: Reuses existing server logic (Opus encoding, GIL bypass, streaming loops, interrupt handling)
**Cons**: Requires protocol translation between JSON-RPC and binary protocol

### Pattern 2: Direct Port Proxy
Let client connect to both Go (UI/agent) and Fun-Audio-Chat (audio) independently.

```
Client → Go (port 3001) → UI/agent
Client → Fun-Audio-Chat (port 11235) → audio
```

**Pros**: No protocol translation needed
**Cons**: Breaks "one wire" principle, client needs two WebSocket connections

### Pattern 3: Subprocess Stdio (NOT recommended)
The spec's original callout — Go spawns Python and communicates via stdin/stdout.

**Why not**: Fun-Audio-Chat's server already handles Opus encoding/decoding, GIL bypass, streaming, interrupt handling. Reimplementing this as stdio pipe reinvents the wheel.

## Critical Gotchas

1. **Not a library**: Cannot `from funaudiochat import FunAudioChat` and call `infer_s2s()`. The model uses `transformers` AutoModel API but requires custom streamer and CosyVoice detokenizer.

2. **GPU requirements**: Needs at least 2 CUDA devices by default. If only 1 GPU, must configure carefully.

3. **Binary protocol**: The server uses binary WebSocket messages, not JSON. Any bridge must translate.

4. **Heartbeat**: 30s keepalive prevents idle connection drops. Bridge must forward or handle these.

5. **TTS cache**: Per-session UUID-based cache in `tts_model.model.hift_cache_dict`. Must be initialized/cleared per session.

## References
- GitHub: https://github.com/FunAudioLLM/Fun-Audio-Chat
- Model: https://huggingface.co/FunAudioLLM/Fun-Audio-Chat-8B
- Technical report: Fun-Audio-Chat-Technical-Report.pdf in repo
