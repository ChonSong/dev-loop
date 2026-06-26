# Discord Voice — Technical Reference

## Environment-Specific Details (2026-06-09)

### Host & Container Layout

- **Host:** EndeavourOS (Arch Linux), Intel Core i3-6100U, 4 cores, ~2GB usable RAM, no GPU
- **Container:** Docker `hermes`, `network_mode: host`, runs the Hermes gateway process
- **Hermes home (host):** `/home/sean/.hermes/` (symlinked/mirrored in container)
- **Config:** `/home/hermeswebui/.hermes/home/.hermes/config.yaml` (active config)
- **Source:** `/home/hermeswebui/.hermes/hermes-sync/projects/hermes-agent/` (5651-line Discord adapter)
- **Gateway log:** `/home/hermeswebui/.hermes/logs/gateway.log`
- **Discord connection:** Already established and operational (logged as of 2026-04-29)

### What's Installed vs. What's Needed

✅ Already present:
- `edge-tts` 7.2.7 (TTS engine)
- `ffmpeg` 7.0.2-static at `/home/hermeswebui/.hermes/local/bin/ffmpeg`
- Opus codec loading logic in discord.py adapter
- Complete VoiceReceiver, STT, TTS, slash command code in hermes-agent source
- Discord bot token and running gateway

❌ Not installed (required for voice):
- `discord.py[voice]` — the entire Discord library
- `PyNaCl` — NaCl encryption for voice RTP
- `davey` — DAVE E2EE decryption
- `faster-whisper` — local STT
- `libopus` — system Opus codec (on host)

### Config Values (as of this session)

```yaml
stt:
  enabled: true
  provider: local
  local:
    model: base
    language: ''

tts:
  provider: edge
  edge:
    voice: en-US-AriaNeural

voice:
  auto_tts: false
  beep_enabled: true
  max_recording_seconds: 120
  silence_duration: 3.0
  silence_threshold: 200
```

### VoiceReceiver Key Constants

- SILENCE_THRESHOLD = 1.5s (end of utterance)
- MIN_SPEECH_DURATION = 0.5s (skip noise)
- SAMPLE_RATE = 48000 (Discord native)
- CHANNELS = 2 (stereo)
- KEEPALIVE_INTERVAL = 60s (UDP keepalive)

RTP packet format: 12-byte header + CSRC (if any) + extension (if any) + encrypted payload + 4-byte nonce.
Encryption: `aead_xchacha20_poly1305_rtpsize` (NaCl AEAD with RTP header as AAD).
DAVE E2EE layer on top of NaCl transport encryption.

### Voice Processing Pipeline (code flow)

1. `DiscordAdapter.join_voice_channel()` (line 1891) — connects to VC
2. Creates `VoiceReceiver`, calls `receiver.start()` (line 1914)
3. `_voice_listen_loop()` (line 2115) — polls `receiver.check_silence()` every 200ms
4. `VoiceReceiver._on_packet()` (~line 270) — decrypts RTP, decodes Opus, buffers PCM per SSRC
5. `VoiceReceiver.check_silence()` (~line 460) — detects 1.5s silence, returns `(user_id, pcm_bytes)`
6. `_process_voice_input()` (line 2155) — PCM → WAV via ffmpeg, then STT via faster-whisper
7. `_handle_voice_channel_input()` in `gateway/run.py` (line 10321) — synthetic MessageEvent → agent
8. Agent processes (tools, reasoning, research)
9. `play_tts()` (line 1782) — edge-tts → audio file → `play_in_voice_channel()`
10. `play_in_voice_channel()` (line 1948) — pauses receiver, plays via FFmpegPCMAudio, resumes

### Why NOT openWakeWord (for this environment)

- 4-core CPU, 2GB RAM, no GPU
- openWakeWord adds ~200MB RAM + continuous CPU for inference
- Silence detection (1.5s gap) is sufficient for conversational voice
- Can be added later without architectural changes

### Potential Issues Specific to This Setup

1. **SSH to host not configured** from container — pip install should happen inside the container, not on the host (except `libopus`)
2. **libopus on host** — needed by discord.py's Opus decoder even in container
3. **faster-whisper first run** — auto-downloads model (~150MB for `base`), ensure disk space
4. **Model inference on CPU** — use `base` or `tiny` model; `medium`+ will be too slow on 4 cores

### Verification Commands

After installing dependencies and restarting gateway:

```bash
tail -f ~/.hermes/logs/gateway.log | grep -i "voice\|opus\|whisper"

# Expected on successful VC join:
# "VoiceReceiver started (bot_ssrc=XXXXX)"
# "Joined voice channel **<name>**"
# "SPEAKING event: ssrc=XXXXX -> user=XXXXXXXX"
# "Voice input from user XXXXXXXX: <transcript>"
```
