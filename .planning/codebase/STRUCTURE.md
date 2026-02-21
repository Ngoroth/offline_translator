# Codebase Structure

**Analysis Date:** 2026-02-20

## Directory Layout

```
offline_translator/
├── src/app/                  # Main application source
│   ├── core/                 # Infrastructure layer
│   │   └── audio/            # Audio I/O implementations
│   ├── orchestrator/         # Pipeline and session management
│   ├── services/             # AI service wrappers
│   └── utils/                # Shared utilities
├── tests/                    # Test suites
│   ├── unit/                 # Unit tests (mocked)
│   ├── smoke/                # Smoke tests (initialization)
│   ├── integration/          # Integration tests (wiring)
│   ├── e2e/                  # End-to-end tests (real models)
│   ├── mocks/                # Test mocks and fixtures
│   └── fixtures/             # Test data files
├── scripts/                  # Utility scripts
├── models/                   # AI model storage
│   ├── llm/                  # GGUF language models
│   └── tts/                  # Piper ONNX voice models
├── typings/                  # Type stubs for 3rd party libs
├── logs/                     # Application logs (runtime)
├── config.yaml               # Main configuration file
├── pyproject.toml            # Project metadata and dependencies
└── AGENTS.md                 # AI coding agent instructions
```

## Directory Purposes

**src/app/core/:**
- Purpose: Infrastructure and foundation code
- Contains: Configuration, logging, types, input handlers, audio devices, startup verification
- Key files:
  - `config.py` - Pydantic settings models and YAML loading
  - `types.py` - TypedDict payload definitions
  - `input.py` - Abstract BaseInput and platform implementations (KeyboardInput, EvdevInput, GPIOInput)
  - `logging.py` - Loguru configuration
  - `startup.py` - Pre-flight verification of models and devices

**src/app/core/audio/:**
- Purpose: Audio I/O implementations
- Contains: Recorder, player, and device enumeration
- Key files:
  - `recorder.py` - Native arecord-based recorder for Linux (ALSA)
  - `player.py` - Sounddevice-based audio player
  - `devices.py` - Device enumeration and resolution utilities
  - `__init__.py` - Exports AudioRecorder, AudioPlayer (may have legacy sounddevice recorder)

**src/app/orchestrator/:**
- Purpose: Pipeline and session coordination
- Contains: Translation pipeline workers and session management
- Key files:
  - `orchestrator.py` - Main event loop, PTT handling, barge-in coordination
  - `pipeline.py` - Worker tasks, queues, VAD integration
  - `session.py` - Session dataclass and SessionManager

**src/app/services/:**
- Purpose: AI model wrappers with async interfaces
- Contains: Service classes for STT, LLM, TTS
- Key files:
  - `stt.py` - Faster-Whisper transcription service
  - `llm.py` - llama-cpp translation service
  - `tts.py` - Piper synthesis service with streaming

**src/app/utils/:**
- Purpose: Shared utilities and algorithms
- Contains: VAD, buffering utilities
- Key files:
  - `vad.py` - WebRTC VAD wrapper and SilenceDetector
  - `buffers.py` - Thread-safe AudioRingBuffer

**tests/:**
- Purpose: Comprehensive test coverage
- Contains: Unit, smoke, integration, and e2e tests
- Organization:
  - `unit/` - Fast tests with mocked dependencies
  - `smoke/` - Initialization and wiring tests
  - `integration/` - Service interaction tests
  - `e2e/` - Full pipeline with real models
  - `mocks/` - Reusable mock implementations

**scripts/:**
- Purpose: Development and deployment utilities
- Contains: Model download, hardware diagnostics
- Key files:
  - `download_models.py` - Downloads LLM and TTS models from HuggingFace
  - `hardware_check.py` - Audio device verification
  - `diagnose.py` - System diagnostics

**models/:**
- Purpose: Local AI model storage (not in git)
- Contains: GGUF (LLM) and ONNX (TTS) model files
- Structure:
  - `llm/` - llama.cpp compatible GGUF files
  - `tts/` - Piper ONNX voice models with JSON configs

**typings/:**
- Purpose: Type stubs for libraries without type hints
- Contains: `.pyi` files for sounddevice and other libs

## Key File Locations

**Entry Points:**
- `src/app/main.py`: Main application entry point (async)
- `scripts/download_models.py`: Model download utility

**Configuration:**
- `config.yaml`: Profile-based configuration
- `src/app/core/config.py`: Pydantic settings models (AppSettings, STTSettings, etc.)

**Core Logic:**
- `src/app/orchestrator/orchestrator.py`: Main event loop
- `src/app/orchestrator/pipeline.py`: Worker pipeline and queue management
- `src/app/orchestrator/session.py`: Session state management

**Services:**
- `src/app/services/stt.py`: Speech-to-text service
- `src/app/services/llm.py`: Translation service
- `src/app/services/tts.py`: Text-to-speech service

**Audio:**
- `src/app/core/audio/recorder.py`: Audio recording (arecord-based)
- `src/app/core/audio/player.py`: Audio playback
- `src/app/core/audio/devices.py`: Device enumeration

**Input Handlers:**
- `src/app/core/input.py`: All input implementations (keyboard, evdev, GPIO)

**Testing:**
- `tests/unit/`: Unit tests with mocks
- `tests/integration/`: Integration tests
- `tests/e2e/`: End-to-end tests

## Naming Conventions

**Files:**
- Python modules: `snake_case.py` (e.g., `audio_recorder.py` concept, but actual file is `recorder.py`)
- Test files: `test_{module}.py` (e.g., `test_orchestrator.py`)
- Config files: `snake_case.yaml` or `snake_case.json`

**Directories:**
- Source packages: `snake_case/` (e.g., `orchestrator/`, `services/`)
- Test categories: `snake_case/` (e.g., `unit/`, `integration/`, `e2e/`)

**Classes:**
- Services: `{Name}Service` (e.g., `STTService`, `LLMService`, `TTSService`)
- Input handlers: `{Platform}Input` (e.g., `KeyboardInput`, `EvdevInput`, `GPIOInput`)
- Exceptions: `{Context}Error` (e.g., `AudioDeviceError`, `STTError`, `LLMError`)
- Data classes: `{Name}` (e.g., `Session`, `AudioDevice`)
- Managers: `{Name}Manager` (e.g., `SessionManager`)
- TypedDicts: `{Name}Payload` (e.g., `AudioPayload`, `TextPayload`)

**Functions/Methods:**
- Private methods: `_snake_case` (e.g., `_get_model`, `_run_transcription`)
- Worker tasks: `_{name}_worker` (e.g., `_stt_worker`, `_llm_worker`)
- Async methods: `async def {action}_{noun}` (e.g., `start_session`, `handle_barge_in`)

**Variables:**
- Queues: `{name}_queue` (e.g., `stt_queue`, `llm_queue`)
- Tasks: `{name}_task` (e.g., `vad_task`)
- Events: `{name}_event` (e.g., `cancel_event`, `stop_event`)

## Where to Add New Code

**New Feature (Translation Stage):**
- Service implementation: `src/app/services/{new_service}.py`
- Worker task: Add to `src/app/orchestrator/pipeline.py`
- Queue definition: Add to `TranslationPipeline.__init__()` in `pipeline.py`
- Payload type: Add to `src/app/core/types.py`
- Wire into pipeline: Update worker chain in `pipeline.py`

**New Component/Module:**
- Implementation: `src/app/{layer}/{module}.py`
- Tests: `tests/unit/test_{module}.py`
- Integration: `tests/integration/test_{module}_integration.py`

**New Input Handler:**
- Implementation: Add class to `src/app/core/input.py` extending `BaseInput`
- Factory update: Update `get_input_handler()` in `src/app/main.py`
- Config: Add settings class to `src/app/core/config.py` if needed

**New AI Service:**
- Implementation: `src/app/services/{service}.py`
- Config: Add settings class to `src/app/core/config.py`
- Integration: Add to pipeline initialization in `main.py` and `pipeline.py`

**Utilities:**
- Shared helpers: `src/app/utils/{module}.py`
- Domain-specific: `src/app/core/{domain}.py` if core infrastructure

**Tests:**
- Unit tests: `tests/unit/test_{module}.py`
- Integration tests: `tests/integration/test_{feature}.py`
- E2E tests: `tests/e2e/test_{scenario}.py`
- Mocks: `tests/mocks/mock_{module}.py`

## Special Directories

**models/:**
- Purpose: Local AI model storage
- Generated: No (populated by download script)
- Committed: No (gitignored)
- Structure:
  - `models/llm/*.gguf` - Llama.cpp compatible models
  - `models/tts/*.onnx` + `*.onnx.json` - Piper voice models

**logs/:**
- Purpose: Application log files
- Generated: Yes (at runtime)
- Committed: No (gitignored)
- Format: JSON lines via loguru

**.venv/:**
- Purpose: Python virtual environment (uv managed)
- Generated: Yes (`uv sync`)
- Committed: No

**typings/ and src/typings/:**
- Purpose: Type stubs for external libraries
- Generated: No (manually maintained)
- Committed: Yes
- Used by: basedpyright for type checking

**.planning/codebase/:**
- Purpose: Codebase analysis documents (this file)
- Generated: Yes (by GSD workflow)
- Committed: Yes (part of repository knowledge)

## Configuration Structure

**config.yaml:**
```yaml
current_profile: "profile_name"
profiles:
  profile_name:
    platform: "windows" | "rpi"
    input_mode: "keyboard" | "evdev" | "gpio"
    audio: { ... }
    stt: { ... }
    llm: { ... }
    tts: { ... }
    vad: { ... }
    speaker_a_key: "..."
    speaker_b_key: "..."
    # ...
```

**Adding New Settings:**
1. Add Pydantic model to `src/app/core/config.py`
2. Add field to `AppSettings` class
3. Update `config.yaml` profile(s)
4. Update tests in `tests/unit/test_config*.py`

---

*Structure analysis: 2026-02-20*
