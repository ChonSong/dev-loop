---
name: discord-voice-mode
description: >
  Discord voice channel integration for Hermes Agent — connect to VC, capture user speech via RTP, transcribe with STT (local Whisper or Groq API), process through agent, respond via TTS playback. Covers architecture, dependency setup, provider configuration, and pitfalls. Trigger when the user wants to talk to the bot via Discord voice channels.
---

# Discord Voice Mode

Full voice conversation pipeline: Discord VC → RTP capture → Opus decode → silence detection → STT → agent → TTS → Opus encode → Discord VC.

## Architecture Overview

**Discord voice is network-based, not local.** No microphone or audio hardware needed in the container. Discord captures audio on the user's machine, encrypts it (NaCl + DAVE E2EE), and sends RTP packets to the bot over UDP.

### Pipeline

```
User speaks in Discord VC
  → Discord sends encrypted RTP (opus, 48kHz stereo)
  → VoiceReceiver: decrypt NaCl → decrypt DAVE → Opus decode → PCM buffer
  → Silence detection (1.5s threshold, 0.5s min speech)
  → PCM → WAV (ffmpeg: 48kHz stereo → 16kHz mono)
  → STT transcription (faster-whisper local / Groq / OpenAI / Mistral / xAI / ElevenLabs)
  → Hermes agent processes transcript (full tool access)
  → Agent response text → TTS (edge-tts / ElevenLabs / Piper)
  → FFmpegPCMAudio → Opus encode → Discord VC playback
```

### Key Files

| File | Role |
|------|------|
| `plugins/platforms/discord/adapter.py` | DiscordAdapter + VoiceReceiver (6248 lines) |
| `gateway/run.py` | Voice mode state management, auto voice reply, TTS decision logic |
| `tools/transcription_tools.py` | STT with 6 provider backends |
| `scripts/discord-voice-doctor.py` | Dependency/config diagnostic tool |

## Dependencies

### Install

```bash
# Core voice support
pip install "discord.py[voice]" PyNaCl davey

# Local STT (optional — ~150MB model download on first use)
pip install faster-whisper

# System codec (container)
apt-get install libopus0 libopus-dev
```

### Already Available

- `ffmpeg` at `~/.hermes/local/bin/ffmpeg`
- `edge-tts` Python package (free TTS)
- `openai` Python package (Whisper API)

### Dependency Chain

| Package | Required By | Purpose |
|---------|------------|---------|
| `discord.py[voice]` | Core | Discord bot + voice channel support |
| `PyNaCl` (>=1.5.0) | `discord.py` voice | NaCl transport decrypt (required — `secret.Aead`, not just `secret.SecretBox`) |
| `davey` | VoiceReceiver | DAVE E2EE frame decrypt |
| `libopus` | `discord.opus` | Opus codec encode/decode |
| `faster-whisper` | Local STT | Offline transcription (optional) |

**Gotcha:** `PyNaCl >= 1.5.0` is required for `nacl.secret.Aead` (the AEAD interface used by Discord's `aead_xchacha20_poly1305_rtpsize` mode). Older versions only have `nacl.secret.SecretBox`. The `discord-voice-doctor.py` script checks for this specifically.

## Configuration

### Environment Variables

```bash
# Required
DISCORD_BOT_TOKEN=your_bot_token_here

# Optional — STT providers
GROQ_API_KEY=groq_key          # Fast free-tier STT
OPENAI_API_KEY=sk-...          # Whisper API
MISTRAL_API_KEY=...            # Voxtral
XAI_API_KEY=...                # xAI Grok STT
ELEVENLABS_API_KEY=...         # ElevenLabs Scribe STT + premium TTS

# Optional — voice behavior
DISCORD_ALLOWED_USERS=userid1,userid2   # Comma-separated, empty = everyone
VOICE_TOOLS_PROVIDER=local|groq|openai|mistral|xai|elevenlabs
VOICE_TOOLS_OPENAI_MODEL=whisper-1
```

### Discord Developer Portal Setup

1. Create application → Bot → Add Bot
2. Enable **Privileged Intents**: `MESSAGE CONTENT INTENT`, `SERVER MEMBERS INTENT`
3. OAuth2 URL Generator: scopes `bot`, permissions: `Connect`, `Speak`, `Send Messages`, `Read Message History`
4. Copy bot token → set as `DISCORD_BOT_TOKEN`

### Voice Mode States

Per-channel voice mode (stored in `~/.hermes/gateway_voice_mode.json`):

| Mode | Behavior |
|------|----------|
| `off` | No voice processing |
| `voice_only` | TTS reply only when input was voice |
| `all` | Always reply with TTS |

Set via `/voice on`, `/voice off`, `/voice tts` slash commands (if bot has slash command support enabled).

## STT Providers

| Provider | Speed | Cost | Quality | Setup |
|----------|-------|------|---------|-------|
| `faster-whisper` (local) | Slow on CPU | Free | Good | Auto-downloads `base` model on first run |
| `groq` | Fast | Free tier | Good | Needs `GROQ_API_KEY` |
| `openai` | Medium | Paid | Excellent | Needs `OPENAI_API_KEY` |
| `mistral` | Fast | Paid | Good | Needs `MISTRAL_API_KEY` |
| `xai` | Fast | Paid | Excellent | Needs `XAI_API_KEY` |
| `elevenlabs` | Medium | Paid | Excellent | Needs `ELEVENLABS_API_KEY` |

**Recommended for first setup:** Groq (free, fast, no local model download). Set `VOICE_TOOLS_PROVIDER=groq` + `GROQ_API_KEY`.

**Recommended for fully local:** `faster-whisper` with model `base` or `small`. Set `VOICE_TOOLS_PROVIDER=local`. First run downloads ~150-300MB.

## TTS Pipeline

1. Agent generates text response
2. `_strip_markdown_for_tts()` removes markdown formatting
3. TTS provider generates audio file (mp3/ogg)
4. If bot is in VC → `play_in_voice_channel()` via `FFmpegPCMAudio` + `discord.PCMVolumeTransformer`
5. If bot is NOT in VC → `send_voice()` sends as file attachment
6. VoiceReceiver is paused during playback (echo prevention)

## VoiceReceiver Internals

`VoiceReceiver` (adapter.py:173-530) handles the full capture pipeline:

- **RTP parsing**: Parses Discord RTP packets (version 2, payload type 120)
- **NaCl decrypt**: `aead_xchacha20_poly1305_rtpsize` with 24-byte nonce
- **DAVE decrypt**: E2EE frame decryption (davey library)
- **Opus decode**: Per-SSRC decoder state (`discord.opus.Decoder()`)
- **Silence detection**: 1.5s threshold, 0.5s minimum speech duration
- **SSRC mapping**: Maps RTP SSRC → Discord user_id via SPEAKING events (opcode 5)
- **Auto-mapping**: If SPEAKING event missing after bot rejoin, infers user from sole allowed VC member

### UDP Keepalive

Sends `\xf8\xff\xxfe` every N seconds to prevent Discord from dropping the UDP route after ~60s of silence.

## Pitfalls

1. **No audio hardware needed.** `/dev/snd`, PulseAudio, ALSA — none of this is required. Voice goes over the network via RTP/UDP.

2. **No wake word needed.** Discord has built-in VAD. Users just speak — the bot receives audio only when they're talking. Silence detection handles utterance boundaries.

3. **PyNaCl version matters.** Must be >=1.5.0 for `Aead` interface. `SecretBox` alone is insufficient. The doctor script checks this.

4. **opus codec must be loadable.** Search path: `ctypes.util.find_library("opus")`, then bundled Windows DLL, then common system paths. On Linux: `apt install libopus0`.

5. **VoiceReceiver pause/resume.** Always paused during TTS playback to prevent echo. The `play_in_voice_channel()` method handles this automatically.

6. **STT hallucination filtering.** `tools.voice_mode.is_whisper_hallucination()` filters common Whisper hallucinations (e.g., "Thank you for watching" on silence).

7. **Auto-disconnect.** Bot leaves VC after `VOICE_TIMEOUT` (300s) of inactivity. Reset by any voice activity or TTS playback.

8. **SSRC mapping race condition.** If bot rejoins VC, SPEAKING events may not be re-sent. Auto-mapping handles single-user case.

## Diagnostic Tool

Run the voice doctor to check all dependencies:

```bash
cd ~/.hermes/hermes-agent
.venv/bin/python scripts/discord-voice-doctor.py
```

Checks: discord.py, PyNaCl, davey, faster-whisper, edge-tts, opus codec, ffmpeg, DISCORD_BOT_TOKEN, STT/TTS provider keys, config.yaml voice settings, bot permissions, guild membership.

## First-Time Activation

1. Install deps: `pip install "discord.py[voice]" PyNaCl davey faster-whisper`
2. Set `DISCORD_BOT_TOKEN` in `~/.hermes/.env`
3. Set `GROQ_API_KEY` (recommended) or `VOICE_TOOLS_PROVIDER=local`
4. Run doctor: `python scripts/discord-voice-doctor.py`
5. Restart Hermes gateway
6. Bot joins VC when user runs `/voice join` or auto-joins
7. Users speak → STT → agent → TTS → response plays in VC
