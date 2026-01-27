# Offline Translator Architecture

## Executive Summary

The Offline Translator is a high-performance, low-latency speech-to-speech translation system designed to run entirely offline. It features an async pipeline architecture that enables concurrent processing of audio, text, and speech for near-zero latency. The system is designed with a Hardware Abstraction Layer (HAL) to support multiple platforms (Windows desktop with keyboard PTT, Raspberry Pi with GPIO).

## Technology Stack

| Category | Technology | Version | Justification |
|----------|-----------|---------|---------------|
| **Runtime** | Python | 3.12+ | Modern async support, extensive ML libraries |
| **Package Manager** | uv | Latest | Fast dependency management |
| **STT** | faster-whisper | >= 1.2.1 | Fast speech recognition with VAD |
| **LLM** | llama-cpp-python | >= 0.3.2 | GGUF model inference (Qwen/Llama) |
| **TTS** | piper-tts | >= 1.3.0 | Fast neural TTS (ONNX) |
| **Audio** | sounddevice | >= 0.5.3 | PortAudio bindings for cross-platform I/O |
| **Audio Processing** | numpy | >= 2.4.1 | Efficient audio data manipulation |
| **VAD** | webrtcvad-wheels | >= 2.0.14 | Voice activity detection |
| **Input (Windows)** | pynput | >= 1.8.1 | Keyboard PTT detection |
| **Logging** | loguru | >= 0.7.3 | Structured async logging |
| **Config** | pydantic | >= 2.0.0 | Configuration validation |
| **Testing** | pytest | >= 7.0 | Test framework with async support |

## Architecture Pattern

### Async Pipeline with Hardware Abstraction Layer

The system uses an **async pipeline architecture** that enables concurrent processing of three stages:

1. **Speech-to-Text (STT)**: Captures audio segments and transcribes to text
2. **Translation (LLM)**: Translates text between languages
3. **Text-to-Speech (TTS)**: Converts translated text to audio output

Each stage runs concurrently using Python's `asyncio`, minimizing latency by processing multiple segments in parallel.

### Hardware Abstraction Layer (HAL)

The HAL provides platform-independent interfaces for:

- **Audio I/O**: `src/app/core/audio.py` - Audio capture and playback
- **Input Devices**: `src/app/core/input.py` - PTT input abstraction
- **Output Devices**: `src/app/core/output.py` - Output abstraction

Platform-specific implementations:
- **Windows**: `src/app/core/input_windows.py` - Keyboard PTT using `pynput`
- **Raspberry Pi**: `src/app/hardware/` - GPIO PTT (to be implemented)

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Application Layer                     │
│                      (src/app/main.py)                      │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Async Orchestrator                        │
│                 (Manages concurrent pipeline)                 │
└─────────────┬────────────────────────┬────────────────────────┘
              │                        │                        │
              ▼                        ▼                        ▼
┌─────────────────────┐  ┌──────────────────────┐  ┌─────────────────────┐
│   STT Service      │  │   LLM Service       │  │   TTS Service      │
│  (faster-whisper)  │  │ (llama-cpp-python)  │  │   (piper-tts)      │
└─────────┬───────────┘  └──────────┬───────────┘  └─────────┬───────────┘
          │                         │                         │
          ▼                         ▼                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Hardware Abstraction Layer                     │
├─────────────┬─────────────────────┬───────────────────────────┤
│   Audio     │    Input Device     │    Output Device          │
│  (PortAudio)│  (Keyboard/GPIO)    │   (Audio/Monitor)         │
└─────────────┴─────────────────────┴───────────────────────────┘
```

## Component Overview

### Core Components (`src/app/core/`)

| Component | Purpose | Interface |
|-----------|---------|-----------|
| `audio.py` | Audio capture/playback | `AudioInput`, `AudioOutput` |
| `input.py` | Input device abstraction | `InputDevice` base class |
| `input_windows.py` | Keyboard PTT (Windows) | `KeyboardInput` implementation |
| `output.py` | Output device abstraction | `OutputDevice` base class |

### Services (`src/app/services/`)

| Service | Purpose | Library |
|---------|---------|---------|
| `stt.py` | Speech-to-Text | faster-whisper + WebRTC VAD |
| `translator.py` | Translation | llama-cpp-python (Qwen/Llama) |
| `tts.py` | Text-to-Speech | piper-tts |

### Utilities (`src/app/utils/`)

| Utility | Purpose |
|---------|---------|
| `buffers.py` | Audio/text buffer management for async pipeline |
| `vad.py` | Voice Activity Detection (WebRTC) |

## Data Architecture

### Audio Data Flow

1. **Capture**: Audio captured at 16kHz, mono, float32
2. **Buffer**: Segmented into chunks by VAD (Voice Activity Detection)
3. **STT**: Segments transcribed to text using faster-whisper
4. **Translation**: Text translated using llama-cpp-python
5. **TTS**: Translated text converted to audio using piper-tts
6. **Playback**: Audio output via sounddevice

### Buffer Management

- **Audio Buffers**: Circular buffers for real-time audio capture
- **Text Buffers**: Queue-based for async text processing
- **Output Queues**: Managed by async orchestrator for concurrent processing

## API Design

### Service Interfaces

#### STT Service (`services/stt.py`)
```python
async def transcribe(audio_segment: np.ndarray) -> str
```

#### Translator Service (`services/translator.py`)
```python
async def translate(text: str, from_lang: str, to_lang: str) -> str
```

#### TTS Service (`services/tts.py`)
```python
async def synthesize(text: str, model_path: str) -> np.ndarray
```

### Hardware Interfaces

#### Audio Interface (`core/audio.py`)
```python
class AudioInput:
    async def read() -> np.ndarray
    async def close()

class AudioOutput:
    async def play(audio: np.ndarray)
    async def close()
```

#### Input Device Interface (`core/input.py`)
```python
class InputDevice:
    async def wait_for_press(speaker_id: int) -> None
    async def wait_for_release(speaker_id: int) -> None
    async def is_pressed(speaker_id: int) -> bool
```

## Source Tree

See [Source Tree Analysis](./source-tree-analysis.md) for complete directory structure.

## Development Workflow

### Running the Application
```bash
uv run python src/app/main.py
```

### Testing
```bash
uv run pytest
```

### Linting
```bash
ruff check .
ruff format .
```

### Type Checking
```bash
basedpyright src/
```

## Deployment Architecture

### Configuration Profiles

The application supports multiple deployment profiles in `config.yaml`:

#### Desktop (Windows)
- **Platform**: Windows
- **Input**: Keyboard PTT (Space/Alt)
- **LLM**: Qwen3-4B-Instruct with GPU acceleration
- **STT**: faster-whisper "small" model
- **Use Case**: Development/testing

#### Raspberry Pi (Production)
- **Platform**: Raspberry Pi
- **Input**: GPIO PTT
- **LLM**: Qwen3-1.7B (CPU only)
- **STT**: faster-whisper "tiny" model
- **Use Case**: Edge deployment

### Model Deployment

Models are downloaded to `models/` directory:
- LLM: `models/llm/*.gguf` (Qwen/Llama quantized models)
- TTS: `models/tts/*.onnx` (Piper TTS models)

Models are gitignored and downloaded via `scripts/download_models.py`.

## Testing Strategy

The project has 12 tests organized as:
- **Unit tests**: Individual component testing (audio, input, output, services)
- **Integration tests**: End-to-end pipeline testing

Test framework: pytest with pytest-asyncio for async testing support.

## Security Considerations

- **Privacy First**: No data leaves the device (offline-only)
- **No telemetry**: No external API calls or data collection
- **Model Security**: Models are downloaded from official sources and verified

## Cross-Platform Notes

### Windows Development
- Keyboard PTT via `pynput`
- Audio via PortAudio (sounddevice)
- GPU acceleration for LLM (CUDA)

### Raspberry Pi Deployment
- GPIO PTT to be implemented in `src/app/hardware/`
- Audio via PortAudio
- CPU-only LLM inference

## Future Enhancements

1. **Multi-language Support**: Add more TTS voices and STT languages
2. **Model Optimization**: Fine-tune models for specific language pairs
3. **Web Interface**: Add web-based PTT controls
4. **Custom Voices**: Support custom voice cloning
5. **Cloud Fallback**: Optional cloud-based models for fallback
