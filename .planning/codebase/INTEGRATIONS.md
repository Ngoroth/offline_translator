# External Integrations

**Analysis Date:** 2026-02-17

## APIs & External Services

**AI Model Sources:**
- Hugging Face Hub - Model downloads (used in tests via `huggingface-hub`)
  - Package: `huggingface-hub>=0.20.0`
  - Usage: Downloading models in test fixtures
  - No runtime dependency - models are local GGUF/ONNX files

**Notable:** This is an **offline-first** application with no cloud API dependencies at runtime. All AI inference happens locally.

## Data Storage

**Databases:**
- None detected - Application operates entirely in-memory

**File Storage:**
- Local filesystem only
- Model storage: `models/` directory (gitignored)
  - STT: Whisper models (downloaded on first use by faster-whisper)
  - LLM: GGUF format models (e.g., Qwen3-4B, Qwen3-0.6B)
  - TTS: ONNX format voice models (e.g., libritts_r, denis)

**Configuration Storage:**
- `config.yaml` - Profile-based YAML configuration
- Environment variables with `APP_` prefix

**Logging:**
- Log files: `logs/app.log` (JSON format via loguru)
- Rotation: 10 MB per file
- Retention: 1 week

**Caching:**
- None - All inference is real-time

## Authentication & Identity

**Auth Provider:**
- Not applicable - No user authentication or identity management
- This is a single-user local application

## Monitoring & Observability

**Error Tracking:**
- None - Local log files only

**Logs:**
- Console: Human-readable format to stderr
- File: JSON format with rotation (`logs/app.log`)
- Framework: loguru with structured logging

**Metrics:**
- None - No external monitoring

## CI/CD & Deployment

**Hosting:**
- Target: Raspberry Pi 5 (local deployment)
- Development: Windows workstation

**CI Pipeline:**
- None detected - No GitHub Actions, GitLab CI, etc.

**Deployment:**
- Manual deployment to target hardware
- Scripts available:
  - `scripts/download_models.py` - Download required AI models
  - `scripts/download_0.6b_model.sh` - Shell script for model download
  - `scripts/hardware_check.py` - Verify hardware setup
  - `scripts/diagnose.py` - System diagnostics

## Environment Configuration

**Required Configuration:**
- `config.yaml` must exist with valid profile
- Models must be downloaded to `models/` directory

**Optional Environment Variables:**
- `APP_PLATFORM` - Override platform detection
- `APP_INPUT_MODE` - Override input mode
- `APP_AUDIO_*` - Audio settings overrides
- `APP_STT_*` - STT settings overrides
- `APP_LLM_*` - LLM settings overrides
- `APP_TTS_*` - TTS settings overrides

**Secrets:**
- No secrets required - fully offline application

## Webhooks & Callbacks

**Incoming:**
- None - No web server or API endpoints

**Outgoing:**
- None - No external callbacks

## Hardware Integration

**Audio Devices:**
- Input: USB microphone via ALSA (`plughw:1,0` on Pi) or PortAudio device index
- Output: Built-in audio or USB speakers via ALSA or PortAudio

**Input Methods (Platform-Specific):**

**Windows (Development):**
- Keyboard via `pynput` library
- Keys: Space (Speaker A), Alt (Speaker B)

**Raspberry Pi (Production):**
- **Option 1: evdev** - USB numpad without X server
  - Device: `/dev/input/event1`
  - Keys: KEY_KP5 (Speaker A), KEY_KP6 (Speaker B)
- **Option 2: GPIO** - Hardware buttons
  - Pin 17: Speaker A button
  - Pin 27: Speaker B button
  - Active-low logic with 50ms debounce

**Cross-Platform Abstraction:**
- `app/core/input.py` - HAL factory pattern for input selection
- Runtime selection via `input_mode` config: `keyboard`, `evdev`, or `gpio`

## Network Requirements

**Runtime:**
- None - Fully offline after initial model download

**Development/Setup:**
- Internet required for:
  - Installing packages via uv
  - Downloading models via huggingface-hub
  - Running tests that download models

---

*Integration audit: 2026-02-17*
