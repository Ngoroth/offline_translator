# AGENTS.md

This file provides guidance for AI coding agents working in this repository.

## Knowledge Freshness

**Your training data is outdated** (approximately August 2025). The current date is available
in the environment context (`Today's date` field).

- **Always fetch current documentation** for libraries, APIs, and tools.
- **Python 3.12** is used instead of 3.14 due to ML library compatibility (onnxruntime, faster-whisper).

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.12.x | Runtime |
| uv | Package manager |
| ruff | Linter and formatter |
| basedpyright | Type checker |
| pytest | Testing framework |

## Quick Commands

### Environment Setup
```bash
uv sync --extra dev                  # Install all dependencies
uv run python scripts/download_models.py # Download required AI models
```

### Running
```bash
uv run python src/app/main.py        # Run the translator
```

### Testing
```bash
uv run pytest                        # Run all tests
```

## Project Structure
```
offline_translator/
├── src/app/                         # Main application package
│   ├── core/                        # Hardware & I/O
│   ├── services/                    # AI Model wrappers
│   ├── settings.py                  # Config models
│   └── main.py                      # Entry point
├── tests/
│   ├── unit/                        # Component tests
│   └── integration/                 # Pipeline tests
├── models/                          # GGUF/ONNX models (gitignored)
├── scripts/                         # Utility scripts
├── config.yaml                      # Active configuration
└── pyproject.toml
```

## Hardware & Cross-Platform Notes
- **Windows**: Development platform, uses `pynput` for keyboard PTT.
- **Raspberry Pi**: Target platform, needs `GPIOInput` implementation.
- **Audio**: Standard 16kHz mono float32 for pipeline consistency.
