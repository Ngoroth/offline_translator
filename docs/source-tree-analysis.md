# Source Tree Analysis

## Project Structure

```
offline_translator/
├── .git/                          # Version control
├── .pytest_cache/                 # Pytest cache
├── .ruff_cache/                   # Ruff linter cache
├── .venv/                         # Python virtual environment
├── .gitignore                     # Git ignore patterns
├── .python-version                # Python version pin
├── AGENTS.md                      # AI coding agent guidance
├── ARCHITECTURE.md                # Async pipeline and HAL design
├── config.yaml                    # Main configuration (profiles: desktop_rtx4070, rpi_deployment)
├── models/                        # GGUF/ONNX models (gitignored)
├── package.json                   # Node.js package (minimal, for opencode)
├── package-lock.json              # Node.js lockfile
├── pyproject.toml                 # Python project manifest and tooling
├── README.md                      # Project overview and getting started
├── SCENARIOS.md                   # Interaction patterns (Barge-in, Multi-phrase)
├── scripts/                       # Utility scripts
│   └── download_models.py         # Model download utility
├── src/                           # Application source code
│   └── app/                       # Main application package
│       ├── __pycache__/           # Python bytecode cache
│       ├── core/                  # Hardware & I/O abstraction
│       │   ├── audio.py           # Audio capture/playback interface
│       │   ├── input.py           # Input device abstraction
│       │   ├── input_windows.py   # Keyboard PTT (pynput) implementation
│       │   └── output.py          # Output device abstraction
│       ├── hardware/              # Platform-specific implementations
│       ├── main.py                # Entry point (application bootstrap)
│       ├── services/              # AI Model wrappers
│       │   ├── stt.py            # Speech-to-Text (faster-whisper)
│       │   ├── translator.py      # Translation (llama-cpp-python)
│       │   └── tts.py            # Text-to-Speech (piper-tts)
│       ├── settings.py            # Config models (Pydantic)
│       ├── typings/               # Type stubs
│       └── utils/                 # Helper utilities
│           ├── buffers.py         # Audio/text buffer management
│           └── vad.py            # Voice Activity Detection (WebRTC)
├── tests/                         # Test suite
│   ├── integration/
│   │   └── test_pipeline.py      # End-to-end pipeline tests
│   └── unit/
│       ├── test_audio.py          # Audio interface tests
│       ├── test_buffers.py        # Buffer management tests
│       ├── test_input.py          # Input device tests
│       ├── test_orchestrator.py   # Async orchestrator tests
│       ├── test_output.py         # Output device tests
│       ├── test_settings.py       # Config validation tests
│       ├── test_stt.py           # STT service tests
│       ├── test_translator.py     # Translation service tests
│       ├── test_tts.py           # TTS service tests
│       └── test_vad.py           # VAD tests
├── logs/                          # Application logs
├── _bmad/                         # BMad workflow and configuration
│   ├── bmm/                       # BMad methodology workflows
│   └── core/                      # Core BMad tasks
└── _bmad-output/                  # BMad workflow outputs
    └── planning-artifacts/
        └── bmm-workflow-status.yaml  # Workflow tracking
```

## Critical Directories

| Directory | Purpose | Notes |
|-----------|---------|-------|
| `src/app/` | Main application code | Python package with async pipeline |
| `src/app/core/` | Hardware & I/O abstraction | Platform-independent interfaces |
| `src/app/hardware/` | Platform-specific implementations | GPIO for RPi, keyboard for Windows |
| `src/app/services/` | AI Model wrappers | STT, LLM, TTS services |
| `src/app/utils/` | Helper utilities | Buffers, VAD, common functions |
| `tests/` | Test suite | Unit + integration tests (12 total) |
| `models/` | GGUF/ONNX models | Gitignored, download via script |
| `scripts/` | Utility scripts | Model download, setup tools |
| `config.yaml` | Active configuration | Supports multiple profiles |
| `docs/` | Generated documentation | Project knowledge base |

## Entry Points

- **Main Entry Point:** `src/app/main.py` (Run with: `uv run python src/app/main.py`)

## Key File Locations

- **Configuration:** `config.yaml`, `src/app/settings.py`
- **Services:** `src/app/services/stt.py`, `src/app/services/translator.py`, `src/app/services/tts.py`
- **Hardware Abstraction:** `src/app/core/audio.py`, `src/app/core/input.py`
- **Platform-Specific:** `src/app/hardware/` (for GPIO on RPi)
- **Tests:** `tests/unit/`, `tests/integration/`

## Architecture Pattern

Async Pipeline with Hardware Abstraction Layer (HAL)
- Three concurrent services (STT, LLM, TTS)
- Platform-independent I/O interfaces
- Configurable for Windows (keyboard PTT) or Raspberry Pi (GPIO)
