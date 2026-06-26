# Discord Voice Mode — Environment Notes

## Container State (2026-06-09)

### Installed
- `ffmpeg` 7.0.2-static at `/home/hermeswebui/.hermes/local/bin/ffmpeg`
- `edge-tts` 7.2.7 (Python package)
- `openai` 2.24.0 (Python package)
- `numpy` 2.4.6
- Python 3.12.13 at `/app/venv/bin/python3`

### Missing (need install)
- `discord.py` — not installed
- `PyNaCl` — not installed
- `davey` — not installed
- `libopus` — not installed (system package)
- `faster-whisper` — not installed
- `sounddevice` — not installed (not needed for Discord voice)
- `pyaudio` — not installed (not needed for Discord voice)

### Audio Hardware
- No `/dev/snd/` devices in container
- No PulseAudio/ALSA
- **This is fine** — Discord voice is network-based (RTP/UDP), no local audio needed

### Hermes Config
- Config at `/home/hermeswebui/.hermes/config.yaml`
- STT provider configured: `local` (model: `base`)
- TTS provider: not explicitly set (defaults to edge-tts)
- Discord section present but no token in config.yaml (must be in `.env`)
- Voice mode state file: `~/.hermes/gateway_voice_mode.json` (doesn't exist yet — fresh)

### Key Source Files (non-build copies)
- Adapter: `/home/hermeswebui/.hermes/hermes-agent/plugins/platforms/discord/adapter.py` (6248 lines)
- Gateway runner: `/home/hermeswebui/.hermes/hermes-agent/gateway/run.py` (19738 lines)
- Transcription: `/home/hermeswebui/.hermes/hermes-agent/tools/transcription_tools.py`
- Voice doctor: `/home/hermeswebui/.hermes/hermes-agent/scripts/discord-voice-doctor.py`

### Install Commands

```bash
source /app/venv/bin/activate
pip install "discord.py[voice]" PyNaCl davey
pip install faster-whisper
apt-get update && apt-get install -y libopus0 libopus-dev
```

### Discord Bot Setup Checklist
1. https://discord.com/developers/applications → New Application
2. Bot → Add Bot → Copy Token
3. Privileged Intents → Enable: Message Content, Server Members
4. OAuth2 → URL Generator → Scopes: `bot` → Permissions: Connect, Speak, Send Messages, Read Message History
5. Open generated URL → invite bot to server
6. Set `DISCORD_BOT_TOKEN` in `~/.hermes/.env`
