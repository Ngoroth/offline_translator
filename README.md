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
- **LLM**: `llama-cpp-python` (Qwen 3 GGUF)
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
   This downloads Qwen3 desktop (`4B`) and Raspberry Pi (`0.6B`) model files, plus Piper TTS voices.

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

## Deploy to Raspberry Pi

### Preconditions
- Raspberry Pi is reachable over SSH as `pi@translator` from your machine.
- Local machine has `ssh` and `rsync` available on `PATH`.

### Command
```bash
uv run scripts/deploy.py
```

### What the deploy script does
1. Runs preflight checks for local tools, SSH reachability, and remote `uv` availability.
2. Syncs project files with `rsync` to `/home/pi/offline_translator/` on `pi@translator`.
3. Excludes `.venv/`, `__pycache__/`, `.git/`, and `logs/` from transfer.
4. Runs `uv sync` remotely in the deployed directory.

### Expected output shape
- Stage banners like `[deploy] preflight...`, `[deploy] rsync...`, and `[deploy] remote uv sync...`.
- Final status line: `[deploy] success` or `[deploy] failed: ...` with actionable next steps.
- If `uv` is missing on the Pi, the script prints concise install guidance and a verification command.

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
