# Discord Voice Mode — Container Setup Reference

## Environment

This applies when running Hermes inside the `hermes` Docker container (Debian Trixie, `network_mode: host`).

## ffmpeg — Not on PATH

**Problem:** The container has ffmpeg bundled inside `imageio_ffmpeg` at a non-standard path. The `VoiceReceiver.pcm_to_wav()` static method and `transcription_tools.py` `_find_binary("ffmpeg")` both fail because `ffmpeg` is not on `PATH` and not in the standard search dirs.

**ffmpeg binary path:**
```
/app/venv/lib/python3.12/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2
```

**Fixes applied:**

1. **`plugins/platforms/discord/adapter.py`** — `VoiceReceiver.pcm_to_wav()`: Replace bare `"ffmpeg"` with `shutil.which("ffmpeg") or <absolute_path>`.

2. **`tools/transcription_tools.py`** — `COMMON_LOCAL_BIN_DIRS`: Add the imageio_ffmpeg binary directory so `_find_binary("ffmpeg")` resolves it.

**Verify:**
```bash
python3 -c "import shutil; print(shutil.which('ffmpeg'))"
```

## Opus Codec — Non-Standard Path

**Problem:** `discord.opus.is_loaded()` returns `False` because `ctypes.util.find_library("opus")` doesn't find it.

**Opus path:** `/home/hermeswebui/.hermes/local/lib/libopus.so.0`

**Fix:** The `DiscordAdapter.connect()` method already has fallback logic. If missing: `apt-get install -y libopus0`

## Discord Voice Doctor False Negatives

The voice doctor checks `shutil.which("ffmpeg")` and `ctypes.util.find_library("opus")` — both return `None` in the container. This is a **known false negative** — voice works despite the doctor reporting failures, if the patches above are applied.

## Voice Pipeline

```
User speaks in Discord VC → RTP (NaCl+DAVE encrypted, Opus encoded)
→ VoiceReceiver: RTP parse → NaCl decrypt → DAVE decrypt → Opus decode → PCM
→ Silence detection (1.5s threshold) → utterance complete
→ PCM → ffmpeg → 16kHz mono WAV
→ faster-whisper (base model) → transcript
→ Hermes agent → edge-tts → MP3
→ discord.FFmpegPCMAudio → Opus → Discord VC
```

## Dependencies (pre-installed)

| Package | Version | Purpose |
|---------|---------|---------|
| discord.py | 2.7.1 | Bot + voice |
| PyNaCl | 1.5.0 | RTP encryption |
| davey | 0.1.5 | DAVE E2EE |
| faster-whisper | 1.2.1 | Local STT |
| edge-tts | 7.2.7 | TTS |
| piper-tts | 1.4.2 | Local TTS alt |

## Token Setup

Add to `~/.hermes/.env`:
```
DISCORD_BOT_TOKEN=your-bot-token
DISCORD_ALLOWED_USERS=numeric-user-id-only
```

Use numeric Discord user ID (enable Developer Mode → right-click → Copy User ID).

## Discord Dev Portal Requirements

- Privileged Intents: `Message Content`, `Server Members`
- Bot Permissions: `Connect`, `Speak`, `Send Messages`, `View Channel`

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| "No messaging platforms enabled" | Add `DISCORD_BOT_TOKEN` to `.env`, restart gateway |
| Voice doctor reports ffmpeg missing | False negative — patch transcription_tools.py COMMON_LOCAL_BIN_DIRS |
| Bot connected but no voice response | Use numeric user ID in DISCORD_ALLOWED_USERS |
| STT empty on first run | Auto-downloads whisper `base` model (~150MB) |
