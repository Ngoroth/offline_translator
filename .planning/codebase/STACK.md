# Technology Stack

**Analysis Date:** 2026-02-20

## Languages

**Primary:**
- Python 3.12.x - All application code in `src/app/`

**Secondary:**
- None (pure Python project)

## Runtime

**Environment:**
- Python 3.12.x (specified in `.python-version`)
- Async runtime via `asyncio`

**Package Manager:**
- uv (modern Python package manager)
- Lockfile: `uv.lock` (present)

## Frameworks

**Core:**
- No web framework - this is a standalone desktop/embedded application
- `pydantic` >= 2.0.0 - Data validation and settings management
- `pydantic-settings` >= 2.12.0 - Configuration management with environment variable support

**Testing:**
- `pytest` >= 7.0 - Test framework
- `pytest-asyncio` >= 1.3.0 - Async test support

**Build/Dev:**
- `ruff` >= 0.1.0 - Linting and formatting
- `basedpyright` >= 1.1.0 - Type checking (strict mode)
- `hatchling` - Build backend

## Key Dependencies

**AI/ML Services:**
- `faster-whisper` >= 1.2.1 - Speech-to-text (CTranslate2-optimized Whisper)
- `llama-cpp-python` >= 0.3.16 - LLM inference (GGUF models)
- `piper-tts` >= 1.4.1 - Text-to-speech synthesis
- `webrtcvad-wheels` >= 2.0.14 - Voice Activity Detection

**Audio I/O:**
- `sounddevice` >= 0.5.5 - Cross-platform audio playback (PortAudio wrapper)
- Native `arecord` (ALSA) - Audio recording on Linux/Raspberry Pi via subprocess

**Utilities:**
- `numpy` >= 2.4.1 - Numerical operations, audio processing
- `loguru` >= 0.7.3 - Structured logging with JSON output
- `pyyaml` >= 6.0 - Configuration file parsing

**Platform-Specific:**
- `pynput` >= 1.8.1 - Keyboard input (Windows/Linux with X11)
- `evdev` (optional, Linux only) - Direct USB device input without X server
- `lgpio` (optional, Raspberry Pi only) - GPIO button input

## Configuration

**Environment:**
- YAML-based configuration: `config.yaml`
- Profile-based settings (supports multiple deployment targets)
- Environment variable override with `APP_` prefix via pydantic-settings
- No `.env` file required - all config in YAML

**Build:**
- `pyproject.toml` - Project metadata, dependencies, tool configuration
- `ruff` config: line-length 100, target py312
- `basedpyright` config: strict type checking in `src/`, relaxed in `tests/` and `typings/`

## Platform Requirements

**Development:**
- Python 3.12.x
- uv package manager
- Audio input/output devices
- Windows: keyboard input via pynput

**Production:**
- Raspberry Pi 4 (2GB RAM) or higher
- Linux with ALSA (arecord/aplay)
- USB microphone
- USB numpad or GPIO buttons for PTT
- Speakers/headphones for output

**Model Requirements:**
- STT: Whisper models (tiny/small/medium) - auto-downloaded or local
- LLM: GGUF format models (Qwen3 variants)
- TTS: Piper ONNX models with JSON config

---

*Stack analysis: 2026-02-20*
