# AGENTS.md

This file provides guidance for AI coding agents working in this repository.

## Knowledge Freshness

**Your training data is outdated** (approximately August 2025). The current date is available
in the environment context (`Today's date` field) — check it before making assumptions.

Since several months have passed since your training cutoff:

- **Always fetch current documentation** for libraries, APIs, and tools before using them
- **Do not rely on memorized versions** — packages like `uv`, `ruff`, `pytorch`, `transformers`,
  etc. may have breaking changes or new features
- **Use WebFetch** to retrieve up-to-date information from official docs when:
  - Installing or configuring dependencies
  - Using CLI tools or their options
  - Implementing integrations with external services
  - Answering questions about current best practices

Useful documentation URLs:
- uv: https://docs.astral.sh/uv/
- ruff: https://docs.astral.sh/ruff/
- basedpyright: https://docs.basedpyright.com/
- pytest: https://docs.pytest.org/

When in doubt — look it up. Do not guess.

## Project Overview

Offline speech-to-speech translator for Raspberry Pi.

- **Target Hardware**: Raspberry Pi 4B (8GB RAM), Raspberry Pi 5 (16GB RAM)
- **Supported Languages**: Russian (ru), English (en), Persian/Farsi (fa), Ukrainian (uk)
- **Development OS**: Windows
- **Development Shell**: Git Bash (MINGW) — use Unix-style syntax (`$HOME`, not `%USERPROFILE%`)
- **Deployment OS**: Linux (Raspberry Pi OS)

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.14.2 | Runtime |
| uv | Package manager |
| ruff | Linter and formatter |
| basedpyright | Type checker |
| pytest | Testing framework |

## Quick Commands

### Environment Setup

```bash
uv sync                              # Install prod dependencies
uv sync --extra dev                  # Install with dev dependencies
```

### Code Quality

```bash
uv run ruff check .                  # Run linter
uv run ruff check . --fix            # Auto-fix linting issues
uv run ruff format .                 # Format code
uv run ruff format . --check         # Check formatting without changes
uv run basedpyright                  # Type checking
```

### Testing

```bash
uv run pytest                        # Run all tests
uv run pytest tests/unit/            # Run unit tests only
uv run pytest tests/integration/     # Run integration tests only
uv run pytest tests/test_foo.py      # Run specific test file
uv run pytest tests/test_foo.py::test_bar  # Run single test
uv run pytest -k "keyword"           # Run tests matching keyword
uv run pytest -x                     # Stop on first failure
uv run pytest --lf                   # Run last failed tests
uv run pytest -v                     # Verbose output
uv run pytest --cov=src              # With coverage report
```

### Run Application

```bash
uv run python -m offline_translator  # Run main application
```

## Project Structure

```
offline_translator/
├── src/
│   └── app/                         # Main application package
│       ├── __init__.py
│       ├── settings.py              # Configuration schemas
│       └── ...                      # Application modules
├── tests/
│   ├── conftest.py                  # Shared fixtures
│   ├── unit/                        # Unit tests
│   ├── integration/                 # Integration tests
│   └── fixtures/                    # Test data
├── models/                          # ML models (gitignored)
├── config.yaml                      # Configuration file
├── pyproject.toml
├── README.md
├── AGENTS.md
└── .gitignore
```

## Code Style Guidelines

### Line Length

Maximum **100** characters per line.

### Imports

Order (ruff handles automatically):

1. Standard library
2. Third-party packages
3. Local imports

```python
import os
from pathlib import Path

import numpy as np
from pydantic import BaseModel

from app.core import Engine
```

### Type Hints

Required for all public functions, methods, and class attributes.

```python
def process(audio_path: Path, language: str = "auto") -> str:
    ...
```

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Functions/methods | snake_case | `process_audio()` |
| Variables | snake_case | `audio_buffer` |
| Classes | PascalCase | `AudioProcessor` |
| Constants | UPPER_SNAKE_CASE | `DEFAULT_SAMPLE_RATE` |
| Private | leading underscore | `_internal_method()` |
| Type aliases | PascalCase | `AudioBuffer = np.ndarray` |

### Docstrings (Google Style)

```python
def translate(
    text: str,
    source_lang: str,
    target_lang: str,
    *,
    timeout: float = 30.0,
) -> str:
    """Translate text between supported languages.

    Args:
        text: Input text to translate.
        source_lang: Source language code ('ru', 'en', 'fa', 'uk').
        target_lang: Target language code.
        timeout: Maximum time in seconds for translation.

    Returns:
        Translated text in target language.

    Raises:
        TranslationError: If translation fails or times out.
        UnsupportedLanguageError: If language pair not supported.
    """
```

### Error Handling

- Define custom exceptions inheriting from a base project exception
- Never silently swallow exceptions
- Use logging for error context
- Prefer specific exceptions over generic ones

```python
try:
    result = engine.process(audio)
except ProcessingError as e:
    logger.exception("Processing failed")
    raise
```

## Testing Guidelines

### TDD Approach

1. Write a failing test first
2. Implement minimal code to pass
3. Refactor while keeping tests green

### Test Structure

- Mirror `src/` structure in `tests/`
- Prefix test files with `test_`
- Prefix test functions with `test_`
- Use descriptive names: `test_returns_empty_string_for_silence`

### Fixtures and Mocking

- Define shared fixtures in `conftest.py`
- Use `pytest-mock` for mocking external dependencies
- Keep test audio samples in `tests/fixtures/`
- Mock hardware (microphone, speakers) and ML models in unit tests

### Coverage Target

Aim for **80%+** code coverage on core logic.

## Hardware & Cross-Platform Notes

### Development vs Deployment

- Develop on Windows, deploy on Raspberry Pi OS (Linux ARM64)
- Use `pathlib.Path` for cross-platform file paths
- Test audio I/O on both platforms when possible

### Memory Constraints

- RPi 4B: 8GB RAM available
- RPi 5: 16GB RAM available
- Keep memory usage in mind when loading ML models
- Consider model quantization for better performance

### Audio

- Use cross-platform audio libraries (e.g., `sounddevice`)
- Handle different audio device configurations gracefully

## Dependency Management

- **Start Minimal**: Do NOT install dependencies proactively. Start with a minimal `pyproject.toml`.
- **Just-in-Time Addition**: Only add a dependency to `pyproject.toml` (via `uv add`) when you are about to write the code that imports it.
- **Review Usage**: If you delete code that uses a library, remove the library from `dependencies`.
- **Avoid Bloat**: Prefer standard library solutions over heavy third-party packages for simple tasks.