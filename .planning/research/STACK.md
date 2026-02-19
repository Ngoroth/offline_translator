# Stack Research

**Domain:** Offline Speech-to-Speech Translation
**Researched:** 2026-02-18
**Confidence:** HIGH (official docs + PyPI verified)

## Current Stack Verification

This is a brownfield project with an existing implementation. Research focused on verifying current versions and identifying updates needed for device deployment.

### Version Status Summary

| Package | Current | Latest | Status | Action |
|---------|---------|--------|--------|--------|
| faster-whisper | 1.2.1 | 1.2.1 | ✓ Current | None |
| llama-cpp-python | 0.3.8 | 0.3.16 | ⚠ Behind | Update recommended |
| piper-tts | 1.3.0 | 1.4.1 | ⚠ Behind | Update recommended |
| sounddevice | 0.5.3 | 0.5.5 | ⚠ Behind | Minor update |
| pytest-asyncio | 0.23.0 | 1.3.0 | ⚠ Behind | Major update |
| ruff | >=0.1.0 | 0.15.1 | ⚠ Behind | Update |
| basedpyright | >=1.1.0 | 1.29.5 | ⚠ Behind | Update |

## Recommended Stack

### Core AI Components

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **faster-whisper** | 1.2.1 | STT (Speech-to-Text) | 4x faster than OpenAI Whisper, uses CTranslate2 for efficient inference. int8 quantization reduces memory by ~40%. Silero-VAD V6 integration in latest version improves voice activity detection. **Already current.** |
| **llama-cpp-python** | 0.3.16 | LLM Translation | Python bindings for llama.cpp. v0.3.16 (Aug 2025) includes Gemma 3 support and improved memory management. CPU-optimized for RPi. **Update from 0.3.8.** |
| **piper-tts** | 1.4.1 | TTS (Text-to-Speech) | Fast, local neural TTS optimized for edge devices. v1.4.1 (Feb 2026) includes bug fixes and improved phonemization. **Update from 1.3.0.** |

### Audio I/O

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **sounddevice** | 0.5.5 | Audio I/O | Cross-platform PortAudio bindings. v0.5.5 (Jan 2026) adds explicit_sample_format for WASAPI. Works with ALSA on RPi. **Minor update from 0.5.3.** |
| **webrtcvad-wheels** | 2.0.14 | Voice Activity Detection | Pre-compiled WebRTC VAD. Required by faster-whisper for internal VAD. Already current. |

### Input Handling (Platform-Specific)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **pynput** | 1.8.1 | Keyboard Input (Windows) | Cross-platform keyboard/mouse monitoring. Used for PTT on desktop development. Already current. |
| **evdev** | Latest | Input Events (Linux/RPi) | Linux kernel input event interface. Required for USB numpad/keyboard PTT on RPi. Already in project. |
| **lgpio** | Latest | GPIO Access (RPi) | RPi.GPIO compatibility shim using lgpio backend. Required for hardware button PTT on RPi. Already in project. |

### Configuration & Validation

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **pydantic** | 2.0.0+ | Data Validation | Type-safe configuration models. v2 provides 5-50x faster validation than v1. |
| **pydantic-settings** | 2.12.0+ | Settings Management | Environment variable and YAML config loading. Integrates with Pydantic v2. |
| **pyyaml** | 6.0+ | YAML Parsing | Standard YAML loader for config files. |

### Infrastructure

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **Python** | 3.12.x | Runtime | Required for ML library compatibility (onnxruntime, faster-whisper). 3.13 not yet fully supported by all dependencies. |
| **uv** | 0.10+ | Package Manager | 10-100x faster than pip. Replaces pip, pip-tools, poetry, pyenv. Astral's recommended tool for 2025+. **Already using.** |

## Verification Tooling

### Testing Framework

| Tool | Version | Purpose | Configuration |
|------|---------|---------|---------------|
| **pytest** | 8.0+ | Test Framework | Markers: smoke, integration, e2e, benchmark, slow |
| **pytest-asyncio** | 1.3.0 | Async Test Support | `asyncio_mode = "auto"`, `asyncio_default_fixture_loop_scope = "function"`. v1.3.0 adds pytest 9 support, drops Python 3.9. **Major update from 0.23.0.** |
| **huggingface-hub** | 0.20.0+ | Model Downloads | For downloading test models in CI |
| **soundfile** | 0.13.0+ | Audio File I/O | Debug/test audio file handling |

### Code Quality

| Tool | Version | Purpose | Configuration |
|------|---------|---------|---------------|
| **ruff** | 0.15.1 | Linter + Formatter | Replaces flake8, black, isort. 10-100x faster. Target: py312, line-length: 100. **Update from >=0.1.0.** |
| **basedpyright** | 1.29.5 | Type Checker | Pyright fork with stricter defaults. `typeCheckingMode = "recommended"`, `reportAny = "error"`. **Update from >=1.1.0.** |

### Test Structure (Existing)

```
tests/
├── unit/          # Component tests (mocked models)
├── smoke/         # Quick initialization tests
├── integration/   # Service wiring (mocked inference)
└── e2e/           # Full pipeline with real models
```

## Installation

```bash
# Core dependencies (using uv)
uv sync --extra dev

# Download required AI models
uv run python scripts/download_models.py

# Run verification
uv run pytest                                    # All tests
uv run pytest -m "not slow"                      # Quick tests
uv run pytest -m "smoke or integration"          # CI tests

# Code quality
uv run basedpyright                              # Type check
uv run ruff check .                              # Lint
uv run ruff format .                             # Format
```

## RPi Deployment Stack

### Platform-Specific Considerations

| Concern | Solution | Notes |
|---------|----------|-------|
| **Audio Device** | ALSA device names (`plughw:1,0`) | Use `arecord -l` to list devices |
| **Input Method** | evdev for USB devices, lgpio for GPIO buttons | Requires `udev` rules for non-root access |
| **Model Size** | tiny STT, 0.6B LLM, medium TTS | Fits in 4GB RAM with headroom |
| **Threading** | `thread_count: 8` | Pi 5 has 4 cores × 2 SMT threads |
| **Context Length** | `n_ctx: 512` | Reduced for translation (not conversation) |

### Recommended RPi Model Sizes

| Component | Model | Size | RPi 5 Performance |
|-----------|-------|------|-------------------|
| STT | tiny.en / tiny | ~75MB | ~200ms for short phrases |
| LLM | Qwen3-0.6B-Q4_K_M | ~400MB | ~300ms per translation |
| TTS | libritts_r-medium | ~60MB | ~100ms synthesis |

### Alternative: piper-tts-plus

For RPi 5 specifically, consider **piper-tts-plus** (v1.6.0) which is optimized for Raspberry Pi 4/5:
- Available on piwheels.org
- Same API as piper-tts
- Potentially better ARM optimization

**Decision:** Stick with upstream piper-tts v1.4.1 unless performance issues arise. piper-tts-plus is a fork with less maintenance visibility.

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| faster-whisper | whisper.cpp | When you need C++ native integration or tiny binary size |
| llama-cpp-python | Ollama | When you want a server-based architecture (not suitable for this embedded use case) |
| piper-tts | Coqui TTS | When you need custom voice training (much larger footprint) |
| sounddevice | pyaudio | When you need PortAudio's callback-based API (more complex) |
| uv | poetry | When you need poetry's build system features (slower) |
| evdev | RPi.GPIO | When you only need GPIO (not USB input devices) |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| **Python 3.14** | ML libraries (onnxruntime, faster-whisper) not yet compatible | Python 3.12.x |
| **OpenAI Whisper** | 4x slower, higher memory usage | faster-whisper |
| **transformers library for STT** | Heavier dependency, slower inference | faster-whisper |
| **gTTS** | Requires internet connection | piper-tts |
| **pip** | 10-100x slower than uv | uv |
| **Poetry** | Slower dependency resolution, lockfile issues | uv |

## Version Compatibility Matrix

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| faster-whisper 1.2.1 | CTranslate2 >= 2.0 | Bundled |
| llama-cpp-python 0.3.16 | llama.cpp b5192+ | Built-in |
| piper-tts 1.4.1 | onnxruntime >= 1.0, < 2.0 | Critical for ARM |
| pytest-asyncio 1.3.0 | pytest >= 7.0, Python >= 3.10 | Drops Python 3.9 support |
| sounddevice 0.5.5 | PortAudio | System dependency |

## Sources

- **faster-whisper**: https://github.com/SYSTRAN/faster-whisper/releases — v1.2.1 verified (Oct 2025)
- **llama-cpp-python**: https://github.com/abetlen/llama-cpp-python/releases — v0.3.16 verified (Aug 2025)
- **piper-tts**: https://pypi.org/project/piper-tts/ — v1.4.1 verified (Feb 2026)
- **sounddevice**: https://pypi.org/project/sounddevice/ — v0.5.5 verified (Jan 2026)
- **pytest-asyncio**: https://github.com/pytest-dev/pytest-asyncio/releases — v1.3.0 verified (Nov 2025)
- **ruff**: https://pypi.org/project/ruff/ — v0.15.1 verified (Feb 2026)
- **basedpyright**: https://pypi.org/project/basedpyright/ — v1.29.5 verified
- **uv**: https://github.com/astral-sh/uv — v0.10.4 verified (Feb 2026)
- **Adafruit RPi AI Guide**: https://learn.adafruit.com/local-models-for-translation-speech-wardrobe-on-pi-5/overview — RPi deployment patterns (HIGH confidence)

---
*Stack research for: Offline Speech-to-Speech Translation*
*Researched: 2026-02-18*
