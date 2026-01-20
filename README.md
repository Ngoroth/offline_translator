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
- [Architecture Design](ARCHITECTURE.md) - Deep dive into the async pipeline and HAL.
- [Usage Scenarios](SCENARIOS.md) - Detailed breakdown of interaction patterns (Barge-in, Multi-phrase, etc.).

## Testing
```bash
uv run pytest
```
Includes 16+ tests covering the async orchestrator, streaming logic, and hardware abstraction.
