# Codebase Structure

**Analysis Date:** 2025-02-17

## Directory Layout

```
offline_translator/
├── src/app/                       # Main application package
│   ├── core/                      # Hardware & I/O abstraction
│   │   ├── audio/                 # Audio I/O (player/recorder)
│   │   ├── audio.py               # Legacy audio module (deprecated)
│   │   ├── config.py              # Pydantic settings & YAML loader
│   │   ├── input.py               # Input HAL (keyboard/evdev/GPIO)
│   │   ├── logging.py             # loguru setup
│   │   ├── output.py              # Output abstraction base
│   │   ├── output_console.py      # Console output implementation
│   │   └── types.py               # TypedDict payloads
│   ├── hardware/                  # Platform-specific hardware (empty)
│   ├── orchestrator/              # Pipeline & session management
│   │   ├── orchestrator.py        # Main event loop coordinator
│   │   ├── pipeline.py            # 4-stage async pipeline
│   │   └── session.py             # Session state & manager
│   ├── services/                  # AI Model wrappers
│   │   ├── stt.py                 # faster-whisper STT service
│   │   ├── llm.py                 # llama-cpp-python LLM service
│   │   └── tts.py                 # piper-tts TTS service
│   ├── utils/                     # Utilities
│   │   ├── buffers.py             # AudioRingBuffer
│   │   └── vad.py                 # WebRTC VAD wrapper
│   ├── __init__.py
│   └── main.py                    # Application entry point
├── tests/                         # Test suite
│   ├── unit/                      # Component tests (isolated)
│   ├── integration/               # Service wiring tests
│   ├── smoke/                     # Quick initialization tests
│   ├── e2e/                       # Full pipeline tests
│   ├── fixtures/                  # Test data (empty)
│   ├── mocks/                     # Test mocks
│   │   ├── mock_audio.py
│   │   ├── mock_gpio.py
│   │   └── mock_input.py
│   └── __init__.py
├── scripts/                       # Utility scripts
│   ├── check_model.py
│   ├── diagnose.py
│   ├── download_models.py
│   ├── hardware_check.py
│   ├── test_recorder.py
│   └── download_0.6b_model.sh
├── models/                        # Model storage (gitignored)
│   ├── llm/                       # GGUF models
│   └── tts/                       # ONNX TTS models
├── logs/                          # Application logs (gitignored)
├── typings/                       # Type stubs for 3rd party libs
│   └── lgpio/
├── config.yaml                    # Active configuration
├── pyproject.toml                 # Python project config
└── docs/                          # Documentation
    ├── architecture.md
    ├── development-guide.md
    ├── raspberry-pi-setup.md
    └── source-tree-analysis.md
```

## Directory Purposes

**`src/app/core/`:**
- Purpose: Hardware abstraction and shared infrastructure
- Contains: I/O interfaces, configuration, logging, type definitions
- Key files: `input.py`, `config.py`, `audio/recorder.py`, `audio/player.py`

**`src/app/orchestrator/`:**
- Purpose: Translation pipeline orchestration
- Contains: Event loop coordination, session management, worker tasks
- Key files: `pipeline.py`, `orchestrator.py`, `session.py`

**`src/app/services/`:**
- Purpose: AI model service wrappers
- Contains: STT, LLM, TTS service classes
- Key files: `stt.py`, `llm.py`, `tts.py`

**`src/app/utils/`:**
- Purpose: Reusable utilities
- Contains: Audio buffers, VAD service
- Key files: `buffers.py`, `vad.py`

**`tests/`:**
- Purpose: Test suite organized by scope
- Structure: `unit/` (isolated), `smoke/` (init), `e2e/` (real models)
- Special: `mocks/` for test doubles

**`models/`:**
- Purpose: Model storage (not committed)
- Structure: `llm/*.gguf`, `tts/*.onnx`
- Generated: No (downloaded via scripts)
- Committed: No (gitignored)

**`scripts/`:**
- Purpose: Development and deployment utilities
- Contains: Model downloaders, diagnostics, hardware checks

**`typings/`:**
- Purpose: Type stubs for libraries without type support
- Contains: `lgpio/__init__.pyi`

## Key File Locations

**Entry Points:**
- `src/app/main.py`: Application entry point
- `src/app/__init__.py`: Package marker

**Configuration:**
- `config.yaml`: Active profile configuration (YAML with Pydantic validation)
- `pyproject.toml`: Build config, dependencies, tool settings
- `src/app/core/config.py`: Settings models and loader

**Core Logic:**
- `src/app/orchestrator/pipeline.py`: Main translation pipeline
- `src/app/orchestrator/orchestrator.py`: Event loop coordinator
- `src/app/core/input.py`: Input abstraction (PTT handling)
- `src/app/core/audio/recorder.py`: ALSA-based audio capture
- `src/app/core/audio/player.py`: Sounddevice audio playback

**Services:**
- `src/app/services/stt.py`: Speech-to-text (faster-whisper)
- `src/app/services/llm.py`: Translation (llama-cpp-python)
- `src/app/services/tts.py`: Text-to-speech (piper-tts)

**Testing:**
- `tests/unit/`: Component tests following `test_*.py` pattern
- `tests/mocks/mock_input.py`: Mock PTT input for testing
- `tests/e2e/conftest.py`: Real model fixtures for E2E

## Naming Conventions

**Files:**
- Modules: `snake_case.py` (e.g., `input.py`, `pipeline.py`)
- Tests: `test_*.py` pattern (e.g., `test_stt.py`)
- Fixtures: Descriptive names (e.g., `synthetic_audio_generator`)

**Directories:**
- Source: `lowercase/` (e.g., `services/`, `orchestrator/`)
- Tests by scope: `unit/`, `integration/`, `smoke/`, `e2e/`

**Classes:**
- Services: `*Service` (e.g., `STTService`, `LLMService`)
- Abstract bases: `Base*` or `*Provider` (e.g., `BaseInput`, `OutputProvider`)
- Pipeline components: `TranslationPipeline`, `SessionManager`

**Functions:**
- Private: `_leading_underscore` (e.g., `_vad_worker`)
- Async: `async def` pattern throughout (e.g., `async def transcribe`)
- Workers: Named by stage (e.g., `_stt_worker`, `_llm_worker`)

## Where to Add New Code

**New AI Service:**
- Primary code: `src/app/services/<service_name>.py`
- Settings: Add model to `src/app/core/config.py`
- Tests: `tests/unit/test_<service_name>.py`

**New Input Method:**
- Implementation: `src/app/core/input.py` (add class inheriting `BaseInput`)
- Settings: Add config fields to `InputSettings` in `config.py`
- Factory: Update `get_input_handler()` in `src/app/main.py`

**New Pipeline Stage:**
- Worker: Add `_<stage>_worker()` method to `TranslationPipeline` in `pipeline.py`
- Queue: Add new queue field and initialization in `__init__`
- Payload: Add TypedDict in `src/app/core/types.py` if new data type

**New Audio Backend:**
- Implementation: `src/app/core/audio/<backend>.py`
- Interface: Follow `AudioRecorder`/`AudioPlayer` patterns
- Factory: Update initialization in `src/app/main.py`

**Utilities:**
- Shared helpers: `src/app/utils/<name>.py`
- Audio-specific: `src/app/core/audio/` if related to I/O

## Special Directories

**`models/`:**
- Purpose: Model storage
- Generated: No (downloaded externally)
- Committed: No (in `.gitignore`)
- Required for: Runtime operation

**`logs/`:**
- Purpose: Application log files
- Generated: Yes (at runtime)
- Committed: No (in `.gitignore`)
- Managed by: `src/app/core/logging.py`

**`.venv/`:**
- Purpose: Python virtual environment
- Generated: Yes (by `uv`)
- Committed: No (partially in `.gitignore`)

**`__pycache__/`:**
- Purpose: Python bytecode cache
- Generated: Yes (automatic)
- Committed: No (in `.gitignore`)

---

*Structure analysis: 2025-02-17*
