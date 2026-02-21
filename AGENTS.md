# AGENTS.md

This file provides guidance for AI coding agents working in this repository.

## Global Mandates

- **Zero Lint/Type Issues**: You MUST fix all issues reported by `ruff` and `basedpyright`.
- **No Ignores**: You are STRICTLY FORBIDDEN from adding `# noqa`, `# type: ignore`, or any other lint/type suppression comments.
- **Test Integrity**: You are STRICTLY FORBIDDEN from deleting or disabling existing tests. Fix the code or the tests instead.
- **Proactiveness**: If you see a linting or typing issue, fix it immediately as part of your task.

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

### Validation
```bash
uv run basedpyright                  # Mandatory type check
uv run ruff check .                  # Mandatory lint check
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
- **Raspberry Pi 4 (2GB RAM)**: Target platform with USB mic, USB numpad (PTT via evdev), and speakers.
- **Audio**: Standard 16kHz mono float32 for pipeline consistency.
