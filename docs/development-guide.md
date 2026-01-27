# Development Guide

## Prerequisites

- **Python:** 3.12+
- **C++ Build Tools:** Required for `llama-cpp-python` compilation
- **uv:** Fast Python package manager ([install guide](https://docs.astral.sh/uv/))

## Installation

1. **Clone repository:**
   ```bash
   git clone <repository-url>
   cd offline_translator
   ```

2. **Install dependencies:**
   ```bash
   uv sync --extra dev
   ```

3. **Download AI models:**
   ```bash
   uv run python scripts/download_models.py
   ```

## Environment Setup

The project uses `uv` for package management, which automatically creates and manages a virtual environment at `.venv/`.

**Configuration:** Edit `config.yaml` to select your profile:
- `desktop_rtx4070` - Windows development with GPU acceleration
- `rpi_deployment` - Raspberry Pi deployment

## Development Commands

### Running the Application

```bash
# Main entry point
uv run python src/app/main.py
```

### Testing

```bash
# Run all tests
uv run pytest

# Run with coverage (if pytest-cov is installed)
uv run pytest --cov=src/app

# Run specific test file
uv run pytest tests/unit/test_audio.py
```

### Linting and Type Checking

```bash
# Lint and format code
ruff check .
ruff format .

# Type checking
basedpyright src/
```

### Model Management

```bash
# Download AI models
uv run python scripts/download_models.py
```

## Project Structure

- `src/app/` - Main application code
  - `core/` - Hardware & I/O abstraction
  - `services/` - AI Model wrappers
  - `utils/` - Helper utilities
- `tests/` - Unit and integration tests
- `models/` - GGUF/ONNX models (gitignored)
- `scripts/` - Utility scripts
- `config.yaml` - Application configuration

## Configuration Profiles

The application supports multiple profiles in `config.yaml`:

### desktop_rtx4070 (Development)
- Platform: Windows
- Input: Keyboard PTT (Space/Alt)
- LLM: Qwen3-4B-Instruct with GPU layers
- STT: faster-whisper "small" model
- Sample rate: 16kHz mono

### rpi_deployment (Production)
- Platform: Raspberry Pi
- Input: GPIO PTT
- LLM: Qwen3-1.7B (CPU only)
- STT: faster-whisper "tiny" model
- Sample rate: 16kHz mono

## Testing Strategy

The project has 12 tests covering:
- Unit tests for individual components (audio, input, output, services)
- Integration tests for the async pipeline
- Test framework: pytest with pytest-asyncio for async support

## Code Style

- **Line length:** 100 characters (configured in ruff)
- **Type checking:** Strict mode with basedpyright
- **Python version:** 3.12+

## Common Development Tasks

### Adding a New Language Pair

Edit `config.yaml`:
```yaml
speakers:
  c:
    name: "Speaker C"
    from_lang: "German"
    to_lang: "English"
    tts_model: "models/tts/en_US-libritts_r-medium.onnx"
```

### Switching STT/LLM Models

Update the corresponding section in `config.yaml`:
```yaml
stt:
  model_path: "small"  # or "tiny", "base", "medium", "large"

llm:
  model_path: "models/llm/your-model.gguf"
  n_gpu_layers: -1  # -1 for all GPU, 0 for CPU only
```

### Adding GPIO Input for RPi

Implement `GPIOInput` in `src/app/hardware/` following the `Input` interface from `src/app/core/input.py`.

## Hardware Notes

- **Windows:** Uses `pynput` for keyboard PTT (Space/Alt)
- **Raspberry Pi:** Requires GPIO implementation in `src/app/hardware/`
- **Audio:** Standard 16kHz mono float32 for pipeline consistency
