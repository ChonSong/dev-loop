---
name: discord-voice
description: Discord voice channel interaction — join/leave VC, receive voice input (Opus/STT), send TTS responses. Covers the full voice pipeline from RTP capture to agent response. Use when the user wants to talk to the bot in a Discord voice channel, set up voice interaction, or troubleshoot voice issues.
always: false
---

# Discord Voice Interaction

Full-duplex voice conversation with the Hermes agent in Discord voice channels. The hermes-agent codebase has a complete built-in voice pipeline — this skill covers how to enable, use, and troubleshoot it.

## Architecture

```
User speaks in Discord VC
  → Discord sends RTP packets (Opus, NaCl/DAVE encrypted)
    → VoiceReceiver: NaCl decrypt → DAVE decrypt → Opus decode → PCM buffer
      → Silence detection (1.5s gap = end of utterance)
        → PCM → WAV (ffmpeg, 48kHz stereo → 16kHz mono)
          → faster-whisper STT (local, base model)
            → Synthetic MessageEvent → agent session (tools, reasoning, research)
              → Agent responds (text)
                → edge-tts (en-US-AriaNeural) → audio
                  → FFmpegPCMAudio → Discord VC
```

## Prerequisites — Install Dependencies

The voice pipeline code exists in the hermes-agent codebase but runtime dependencies are NOT installed by default:

```bash
pip install "discord.py[voice]" PyNaCl davey faster-whisper
```

System dependency (on the host, not in the container):
```bash
# EndeavourOS / Arch
sudo pacman -S opus

# Debian / Ubuntu
apt install libopus0
```

**Verify:**
```bash
python3 -c "import discord; print(discord.__version__)"
python3 -c "import nacl; print(nacl.__version__)"
python3 -c "import davey; print(davey.__version__)"
python3 -c "import faster_whisper; print(faster_whisper.__version__)"
python3 -c "import discord.opus; discord.opus.load_opus('opus'); print('Opus OK')"
```

## Discord Bot Permissions

The bot needs these OAuth2 scopes/permissions:
- **Scopes:** `bot`, `applications.commands`
- **Permissions:** `Connect`, `Speak`, `Send Messages`, `Read Message History`

Verify at: `https://discord.com/developers/applications/<APP_ID>/bot`

## Configuration

In `~/.hermes/config.yaml`:

```yaml
stt:
  enabled: true
  provider: local
  local:
    model: base        # tiny, base, small, medium, large-v3
    language: ''       # empty = auto-detect

tts:
  provider: edge
  edge:
    voice: en-US-AriaNeural

voice:
  auto_tts: false      # true = voice-reply to ALL messages in VC-linked channels
```

## Usage (via Discord Slash Commands)

| Command | Effect |
|---------|--------|
| `/voice join` | Bot joins your current voice channel |
| `/voice leave` | Bot disconnects from voice |
| `/voice on` | Voice reply when user sends voice input |
| `/voice tts` | Voice reply to ALL messages (text + voice) |
| `/voice off` | Text-only mode (default) |
| `/voice status` | Show current mode |

## Session Binding

When the bot joins a VC, it binds to the text channel where `/voice join` was invoked. Voice input from the VC is processed through the same agent session as that text channel. The agent has full tool access — it can research, investigate, run code, etc. — and responds with TTS audio in the VC.

## Key Code Locations

| Component | File | Lines |
|-----------|------|-------|
| VoiceReceiver (RTP/Opus/PCM) | `gateway/platforms/discord.py` | 152–500 |
| Voice listen loop + STT dispatch | `gateway/platforms/discord.py` | 2115–2188 |
| Voice input → agent pipeline | `gateway/run.py` | 10321–10387 |
| TTS playback in VC | `gateway/platforms/discord.py` | 1948–1989 |
| STT transcription | `tools/transcription_tools.py` | 1–936 |
| Whisper hallucination filter | `tools/voice_mode.py` | 1–1018 |
| Slash commands | `gateway/platforms/discord.py` | 3000–3014 |

Source: `/home/hermeswebui/.hermes/hermes-sync/projects/hermes-agent/`

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| "Opus codec not found" warning | `libopus` not installed on host | `sudo pacman -S opus` |
| "Voice dependencies missing" | PyNaCl/davey not installed | `pip install PyNaCl davey` |
| No voice received | Bot lacks `Connect`/`Speak` permissions | Re-invite bot with correct perms |
| Whisper hallucinates on silence | Normal — filtered automatically | `is_whisper_hallucination()` already filters common patterns |
| TTS echoes back into receiver | Should not happen — receiver pauses during playback | Check `receiver.pause()` / `receiver.resume()` in `play_in_voice_channel()` |
| VoiceReceiver misses SPEAKING events after rejoin | Known edge case | Auto-inference maps SSRC to sole allowed member |
| STT is slow | CPU inference, base model | Normal: ~2-3s for 5s utterance on 4 cores. Use `tiny` model for speed. |

## Wake Word (Optional Future Enhancement)

openWakeWord is **not needed initially** — silence detection (1.5s gap) works well for conversational voice. To add wake word later:

```bash
pip install openwakeword
```

Then add wake word detection on the PCM buffer before triggering STT. Adds ~200MB RAM and significant CPU overhead — evaluate on constrained hosts.

## Environment Notes

- The Hermes gateway runs in a Docker container (`hermes`) — no local audio hardware needed (all voice is network/RTP)
- ffmpeg is at `/home/hermeswebui/.hermes/local/bin/ffmpeg`
- The Discord gateway is already connected and operational
- 4 CPU cores, ~2GB RAM available — sufficient for whisper `base` model (~150MB)
- No GPU — whisper runs on CPU (fast enough for conversational use with `base` model)
