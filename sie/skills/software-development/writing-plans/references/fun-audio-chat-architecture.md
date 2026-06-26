# Fun-Audio-Chat Architecture Notes

## What It Is
A Large Audio Language Model (8B params) for natural, low-latency voice interactions. Built by Alibaba Cloud (FunAudioLLM). Apache-2.0 license.

## Key Architecture Facts (Verified 2026-05-10)

### Not a Subprocess — It's a WebSocket Server
The spec often describes "Go spawns Python subprocess for Fun-Audio-Chat." **This is wrong.** The repo ships a full `aiohttp` WebSocket server at `web_demo/server/server.py` on port 11235.

### Server Architecture
- **Framework**: `aiohttp` + `asyncio` for WebSocket
- **Endpoint**: `GET /api/chat`
- **Concurrency**: `multiprocessing.Process` for TTS (bypasses GIL)
- **Model Loading**: `GlobalModelManager` singleton — loads once, shares across sessions
- **Communication**: `asyncio.Queue`, `queue.Queue`, `mp.Queue` for non-blocking data flow

### Binary Protocol
Messages are binary, not JSON. Protocol defined in `web_demo/server/protocal.py`:

| Message Type | Hex | Purpose |
|---|---|---|
| HANDSHAKE | 0x00 | Sent on connect (version + model) |
| AUDIO | 0x01 | Raw Opus payload |
| TEXT | 0x02 | Text input/output |
| CONTROL | 0x03 | START/PAUSE/END_TURN/RESTART |
| METADATA | 0x04 | Custom metadata (e.g., system_prompt) |
| ERROR | 0x05 | Error messages |
| PING | 0x06 | Keep-alive |

Control messages:
| Control | Hex | Purpose |
|---|---|---|
| START | 0x00 | Begin recording/processing |
| END_TURN | 0x01 | End of user turn |
| PAUSE | 0x02 | Interrupt mid-inference |
| RESTART | 0x03 | Restart session |

### Audio Pipeline
1. Input: Opus stream → `sphn.OpusStreamReader` → PCM → Resample (24kHz → 16kHz) → WAV
2. Inference: Chat template → `FunaudioChatStreamer` → text + audio tokens
3. TTS: Audio tokens → `mp.Queue` → `tts_worker_process` (GPU) → generated audio
4. Output: Buffer → `sphn.OpusStreamWriter` (80ms frames) → WebSocket at ~10ms intervals
5. Text: Sent separately at 200ms intervals (waits for first audio frame)

### GPU Requirements
- **Default**: 2 CUDA devices (cuda:0 for S2S model, cuda:1 for TTS)
- **Model config**: Forces `torch.bfloat16`, disables `output_router_logits` for Qwen3 MoE
- **Frame size**: 1920 samples @ 24kHz (80ms)

### Dependencies (requirements.txt)
- `transformers==4.52.3`, `torch`, `torchaudio`
- `sphn` (Opus codec)
- `onnxruntime-gpu==1.18.0` (Linux)
- `tensorrt-cu12` (Linux, for TTS acceleration)
- `librosa`, `soundfile` (audio I/O)
- `aiohttp`, `uvicorn==0.30.0` (server)

### Bridge Design Implications
When integrating Fun-Audio-Chat into a Go backend:
1. **Don't use stdio** — it's a WebSocket server, not a CLI tool
2. **Don't reimplement the protocol** — connect to its server and relay
3. **Handle the binary protocol** — encode/decode MessageType + payload
4. **Interrupt is built-in** — send `CONTROL:PAUSE` (0x03, 0x02) to abort mid-inference
5. **GPU planning** — need 2 GPUs for full performance, or configure single-GPU mode

### Inference API (Python)
```python
from funaudiochat.register import register_funaudiochat
register_funaudiochat()

from transformers import AutoModelForSeq2SeqLM, AutoProcessor

model = AutoModelForSeq2SeqLM.from_pretrained(model_path, torch_dtype=torch.bfloat16)
processor = AutoProcessor.from_pretrained(model_path)
```

### Web Demo Client
The repo includes a full web demo client (React + TypeScript) at `web_demo/client/` with:
- `audio-processor.ts` — audio capture/processing
- `SocketContext.ts` — WebSocket connection management
- `AudioVisualizer` — real-time audio visualization
- Binary protocol encoder/decoder in `src/protocol/`
