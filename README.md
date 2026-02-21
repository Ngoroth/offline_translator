# Neuromancer Pi: Offline Translator

High-performance, configurable offline speech-to-speech translator designed for low-latency real-time dialogue.

## Features
- **Offline First**: All processing (STT, LLM, TTS) happens locally on your machine or edge device.
- **Async Pipeline**: Concurrent processing of audio, text, and speech for near-zero latency.
- **Intelligent Dual PTT**: 
  - Supports two speakers with dedicated keys (**Space** and **Alt**).
  - Handles pauses automatically: speaks and translates in segments while you hold the button.
- **Barge-in Support**: Interrupt the machine at any time by pressing a PTT key; it stops immediately and starts listening.
- **Privacy Driven**: No data ever leaves the device.

## Tech Stack
- **Python**: 3.12+
- **STT**: `faster-whisper` with VAD (WebRTC)
- **LLM**: `llama-cpp-python` (Qwen 2.5 / Llama 3)
- **TTS**: `piper-tts` (ONNX)
- **Audio**: `sounddevice`, `numpy`

## Installation

1. **Prerequisites**:
   - Install [uv](https://docs.astral.sh/uv/).
   - Install C++ Build Tools (for `llama-cpp-python`).

2. **Setup**:
   ```bash
   uv sync --extra dev
   ```

3. **Download Models**:
   ```bash
   uv run python scripts/download_models.py
   ```

## Usage

1. **Run**:
   ```bash
   uv run python src/app/main.py
   ```

2. **Controls**:
   - **Speaker A (Space)**: English -> Russian (Default).
   - **Speaker B (Alt)**: Russian -> English (Default).
   - **Hold** to speak, **Release** to hear the translation.
   - You can make pauses while holding the key; the system will process segments in the background.

## Documentation
- [Usage Scenarios](SCENARIOS.md) - Detailed breakdown of interaction patterns (Barge-in, Multi-phrase, etc.).

## Testing
The project uses `pytest` with markers for different test levels.

### Quick Tests (CI)
Run unit, smoke, and integration tests (~15s):
```bash
uv run pytest -m "not e2e"
```

### Full E2E Suite (Nightly)
Run everything including real model tests (~60s+). Requires ~535MB model download on first run.
```bash
uv run pytest -m "e2e"
```

### Performance Benchmarks
Validate NFRs (Latency ≤1.0s, VAD ≤200ms):
```bash
uv run pytest -m "benchmark"
```

### Test Directory Structure
- `tests/unit`: Component logic (fast)
- `tests/smoke`: Service initialization and mocking (fast)
- `tests/integration`: Pipeline wiring and contracts (medium)
- `tests/e2e`: Full system with real AI models (slow)
