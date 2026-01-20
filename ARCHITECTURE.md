# Architecture Design Document: "Neuromancer Pi"

## System Overview
High-performance, configurable offline speech-to-speech translator designed for low-latency real-time dialogue.

The system is built on a **Hardware Agnostic Architecture**, capable of scaling from embedded edge devices (Raspberry Pi 5) to high-end workstations (NVIDIA GPUs). It uses a profile-based configuration system to adapt its AI models and hardware interfaces to the available resources.

**Key Goals:**
*   **Low Latency:** Streaming architecture for real-time interaction.
*   **Privacy:** Fully offline processing.
*   **Flexibility:** Configurable models, voices, and hardware backends.

## Architecture & Configuration

The system behavior is defined by **Configuration Profiles** (`config.yaml`). This allows the same codebase to run on vastly different hardware by swapping components at runtime.

### Hardware Abstraction Layer (HAL)
The application interfaces with hardware through abstract protocols, selected via configuration:

1.  **Input Interface (`InputProvider`):**
    *   *GPIO Mode:* Uses physical buttons (e.g., for Raspberry Pi).
    *   *Keyboard Mode:* Uses hotkeys (e.g., Spacebar) for development/desktop use.

2.  **Compute Backend (`InferenceEngine`):**
    *   *CPU/Neon:* Optimized for ARM64/Edge devices.
    *   *CUDA/Metal:* Offloads processing to discrete GPUs for high-performance nodes.

## Technology Stack

### 1. Intelligence Layer (The Brain)
*   **Engine:** `llama.cpp` (Python bindings).
*   **Model:** Configurable GGUF models.
    *   *Edge Profile:* Qwen 2.5-3B / Qwen 3 (Quantized q4_k_m).
    *   *Desktop Profile:* Qwen 2.5-14B/72B or Llama 3.
*   **Optimization:** Managed **KV-Cache** for dialogue context.
*   **Role:** Context-aware translation, role-playing, slang handling.

### 2. Perception Layer (The Ears)
*   **Engine:** `whisper.cpp` (OpenAI Whisper C++ port).
*   **Mode:** Real-time Streaming.
*   **Model:** Configurable (e.g., `tiny`, `small`, `medium`).
*   **VAD:** Voice Activity Detection (Silero VAD or WebRTC) triggers segment processing.

### 3. Speech Generation (The Voice)
*   **Engine:** `Piper TTS`.
*   **Mode:** Streaming Input (Receives text tokens as they are generated).
*   **Voices:** Configurable ONNX models (supports ru, en, fa, uk).

## Data Pipeline (Asyncio Event Loop)

The application runs as an asynchronous pipeline:

1.  **Audio Capture:**
    *   Reads microphone into a Ring Buffer.
    *   VAD monitors for speech/silence.
    *   **Trigger:** Pause > 0.5s OR Button Release -> Audio Segment -> STT Queue.

2.  **STT Worker:**
    *   Consumes Audio Segment -> Generates Text (Source Language).
    *   Updates `ChatHistory`.

3.  **LLM Worker:**
    *   Consumes Text -> Generates Translation (Token Stream).
    *   Uses system prompt: *"You are a real-time translator. Translate [Lang A] to [Lang B] preserving tone."*

4.  **TTS Worker:**
    *   Consumes Translation Tokens (accumulates by sentence).
    *   Generates Audio Stream -> Playback Queue.

5.  **Playback & Interrupts:**
    *   Plays audio from queue.
    *   **Interrupt Logic:** If PTT button is pressed during playback -> Immediately Stop & Clear Queues.

## Directory Structure
```
src/app/
├── core/
│   ├── stt_stream.py    # Whisper streaming wrapper
│   ├── tts_stream.py    # Piper streaming wrapper
│   └── llm_service.py   # LLM client (KV-cache management)
├── hardware/
│   ├── audio_io.py      # PyAudio Async Reader/Writer
│   ├── input_handler.py # Abstract Input Provider (GPIO/Keyboard)
│   └── device_map.py    # Hardware capability detection
├── utils/
│   ├── vad.py           # Voice Activity Detection logic
│   └── buffers.py       # Ring buffer implementation
├── settings.py          # Configuration & Profile management
└── main.py              # Asyncio Orchestrator
```

## Example Profiles

### Profile A: "Neuromancer Edge" (Production)
*   **Target:** Raspberry Pi 5 (8GB/16GB).
*   **Strategy:** Maximize efficiency within thermal/power limits.
*   **Input:** GPIO (Physical PTT).
*   **Models:** Qwen 2.5-3B (q4_k_m), Whisper Small.

### Profile B: "Desktop Powerhouse" (Development)
*   **Target:** Windows/Linux PC with NVIDIA GPU.
*   **Strategy:** Maximize intelligence and speed.
*   **Input:** Keyboard (Spacebar PTT).
*   **Models:** Qwen 2.5-14B (q4_k_m), Whisper Medium.
