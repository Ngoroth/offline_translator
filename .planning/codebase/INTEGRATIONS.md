# External Integrations

**Analysis Date:** 2026-02-20

## APIs & External Services

**Hugging Face Hub:**
- Model downloads for LLM and TTS
- Access: Public models (no authentication required for download)
- Models hosted:
  - LLM: `bartowski/Qwen_Qwen3-4B-Instruct-2507-GGUF`, `lm-kit/qwen-3-1.7b-instruct-gguf`
  - TTS: `rhasspy/piper-voices` (English, Russian voices)
- Download script: `scripts/download_models.py`

**Faster-Whisper Model Source:**
- Accepts Hugging Face model IDs (e.g., "tiny", "small") or local paths
- Auto-downloads to `~/.cache/huggingface` if using model ID
- Local path: `models/stt/` directory

## Data Storage

**Databases:**
- None - Stateless application

**File Storage:**
- Local filesystem only
- Model files: `models/` directory structure:
  - `models/llm/` - GGUF format LLM models
  - `models/tts/` - Piper ONNX models with JSON configs
  - `models/stt/` - Whisper models (optional, can use HF cache)
- Logs: `logs/app.log` (JSON format, 10MB rotation, 1 week retention)
- Config: `config.yaml`

**Caching:**
- In-memory only (no persistent cache)
- Model instances cached in services after lazy loading

## Authentication & Identity

**Auth Provider:**
- None - Fully offline application
- No user accounts or authentication

## Monitoring & Observability

**Error Tracking:**
- None (local logs only)

**Logs:**
- Structured logging via `loguru`
- Console: human-readable format with colors
- File: JSON format with rotation (`logs/app.log`)
- Features: backtrace, diagnose, async-safe enqueue

## CI/CD & Deployment

**Hosting:**
- Standalone application (no server deployment)
- Target platforms:
  - Development: Windows desktop with RTX GPU
  - Production: Raspberry Pi 4 (headless)

**CI Pipeline:**
- None configured (no `.github/workflows/`)
- Manual validation: `uv run basedpyright` and `uv run ruff check .`

## Environment Configuration

**Required config files:**
- `config.yaml` - Main configuration with profile selection

**Config structure:**
```yaml
current_profile: "profile_name"
profiles:
  profile_name:
    platform: "windows" | "rpi"
    input_mode: "keyboard" | "evdev" | "gpio"
    audio: {...}
    stt: {...}
    llm: {...}
    tts: {...}
    vad: {...}
    speakers: {...}
```

**No secrets management:**
- No API keys required
- No database credentials
- No `.env` files

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

## Hardware Integrations

**Audio Subsystem:**
- Input: `arecord` (ALSA) subprocess on Linux, `sounddevice` for enumeration
- Output: `sounddevice` (PortAudio) for playback
- Format: 16kHz mono float32 throughout pipeline

**Input Methods:**
1. **Keyboard** (Windows/Linux with X11)
   - Library: `pynput`
   - Config: Key names (e.g., "space", "alt")
   
2. **Evdev** (Linux headless)
   - Library: `evdev` (optional dependency)
   - Config: Device path `/dev/input/eventX`
   - Used for USB numpads on RPi without display
   
3. **GPIO** (Raspberry Pi)
   - Library: `lgpio` (optional dependency)
   - Config: GPIO pin numbers, chip ID, debounce settings
   - Active-low configuration for buttons

## Model Management

**Download Process:**
- Run `uv run python scripts/download_models.py`
- Downloads from Hugging Face:
  - LLM: Qwen3-4B (~2.5GB) or Qwen3-1.7B (~1GB) for RPi
  - TTS: Piper English/Russian voices (~60MB each)

**Startup Verification:**
- `StartupVerifier` in `src/app/core/startup.py`
- Validates model files exist before running
- Validates audio devices available
- Exits with actionable error messages if missing

---

*Integration audit: 2026-02-20*
