---
name: discord-voice-setup
description: >-
  Container-specific patches needed for Discord voice mode to work in the Hermes gateway
  (opus codec loading, ffmpeg PATH, zombie lock fix). Run after container rebuilds.
---

# Discord Voice Setup (Container)

When the Hermes container is rebuilt, these patches must be re-applied for Discord voice mode (VC speech → STT → agent → TTS → spoken response).

## Patches Needed

### 1. Opus Codec Path (container libopus at custom path)

**File**: `~/.hermes/home/.local/lib/python3.12/site-packages/plugins/platforms/discord/adapter.py`

Add fallback before `for opus_path in opus_candidates:` (around line 651):

```python
            # Fallback: check absolute path for container deployments
            _hermes_opus = "/home/hermeswebui/.hermes/local/lib/libopus.so.0"
            if os.path.isfile(_hermes_opus):
                opus_candidates.append(_hermes_opus)
```

### 2. ffmpeg Path for VoiceReceiver.pcm_to_wav

**File**: `~/.hermes/home/.local/lib/python3.12/site-packages/plugins/platforms/discord/adapter.py`

Replace `"ffmpeg"` with absolute path fallback (around line 510):

```python
            ffmpeg_bin = shutil.which("ffmpeg") or "/app/venv/lib/python3.12/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"
```

### 3. ffmpeg Path for transcription_tools.py

**File**: `~/.hermes/home/.local/lib/python3.12/site-packages/tools/transcription_tools.py`

Replace the `COMMON_LOCAL_BIN_DIRS` tuple (around line 93) to include the imageio_ffmpeg dir.

### 4. Zombie PID Lock Fix

**File**: `~/.hermes/home/.local/lib/python3.12/site-packages/gateway/status.py`

Change line 656 from:
```python
                                    if _state in {"T", "t"}:  # stopped or tracing stop
```
to:
```python
                                    if _state in {"T", "t", "Z"}:  # stopped, tracing stop, or zombie
```

## Config

- `auto_tts: true` under `voice:` in `~/.hermes/config.yaml`
- `DISCORD_BOT_TOKEN` and `DISCORD_ALLOWED_USERS` in `~/.hermes/.env`
- `stt.provider: local` with `faster-whisper base` model (auto-downloads ~150MB on first use)
- `tts.provider: edge` with `en-US-AriaNeural`

## Starting Gateway

```bash
hermes gateway run   # in background
```
