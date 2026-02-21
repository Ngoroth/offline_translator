# Technology Stack

**Analysis Date:** 2026-02-17

## Languages

**Primary:**
- Python 3.12 - All application logic, services, and orchestration
- YAML - Configuration files (`config.yaml`)

## Runtime

**Environment:**
- Python 3.12.x (see `.python-version`)
- uv - Modern Python package manager and virtual environment tool

**Package Manager:**
- uv with lockfile (`uv.lock`)
- Build system: hatchling

## Frameworks

**Core:**
- Pydantic 2.x - Data validation and settings management (`app/core/config.py`)
- pydantic-settings - Environment-aware configuration
- loguru - Structured logging framework (`app/core/logging.py`)

**Testing:**
- pytest 7.x - Test framework
- pytest-asyncio - Async test support (auto mode enabled)

**Build/Dev:**
- ruff - Linter and formatter (line-length: 100, target py312)
- basedpyright - Type checker (strict mode for src/, relaxed for tests)
- hatchling - Build backend

## Key Dependencies

**Critical AI/ML:**
- `faster-whisper>=1.2.1` - Speech-to-Text using Whisper models
- `llama-cpp-python>=0.3.8` - Local LLM inference via GGUF models
- `piper-tts>=1.3.0` - On-device Text-to-Speech (ONNX-based)
- `numpy>=2.4.1` - Numerical operations for audio processing

**Hardware & Audio:**
- `sounddevice>=0.5.3` - Cross-platform audio I/O
- `pynput>=1.8.1` - Keyboard input handling (Windows development)
- `webrtcvad-wheels>=2.0.14` - Voice Activity Detection

**Data & Config:**
- `pyyaml>=6.0` - YAML configuration parsing

**Development:**
- `huggingface-hub>=0.20.0` - Model downloads in tests
- `soundfile>=0.13.0` - Debug audio file I/O

## Configuration

**Environment:**
- Configuration via `config.yaml` with profile-based settings
- Environment variable prefix: `APP_` (e.g., `APP_PLATFORM`)
- Two profiles: `desktop_rtx4070` (Windows dev) and `rpi_deployment` (Raspberry Pi)

**Key Config Files:**
- `config.yaml` - Main application configuration
- `pyproject.toml` - Project metadata, dependencies, tool configs
- `.python-version` - Python version specification

**Build:**
- `pyproject.toml` contains all tool configurations:
  - `[tool.ruff]` - Linting and formatting
  - `[tool.basedpyright]` - Type checking with strict/relaxed environments
  - `[tool.pytest.ini_options]` - Test configuration with markers

## Platform Requirements

**Development (Windows):**
- Python 3.12.x
- uv package manager
- CUDA support optional (for faster-whisper GPU acceleration)
- Keyboard input via pynput

**Production (Raspberry Pi 5):**
- Python 3.12.x
- ALSA audio subsystem
- Optional: evdev for USB numpad input (used on target device)
- Optional: GPIO for hardware button input (available but not used on target)
- CPU-only inference (GGUF models, ONNX TTS)

**Hardware Requirements:**
- USB microphone (input)
- Speakers or headphones (output)
- Minimum 4GB RAM recommended (varies by model size)
- Storage: ~2GB for models (whisper, LLM, TTS voices)

---

*Stack analysis: 2026-02-17*
