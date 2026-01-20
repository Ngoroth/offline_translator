# Architecture Design Document: "Neuromancer Pi"

## System Overview
High-performance, configurable offline speech-to-speech translator designed for low-latency real-time dialogue. The system is built on an asynchronous, stream-oriented architecture.

**Key Goals:**
*   **Low Latency:** Streaming architecture for real-time interaction (no batching).
*   **Privacy:** Fully offline processing using GGUF and ONNX models.
*   **Flexibility:** Profile-based configuration for different hardware (Edge vs. Desktop).

## Technology Stack
*   **STT (Ears):** `faster-whisper` (streaming mode) with VAD.
*   **LLM (Brain):** `llama-cpp-python` with KV-Cache and token streaming. Using **Qwen 3 Instruct** models (4B for Desktop, 1.7B for Edge).
*   **TTS (Voice):** `Piper TTS` (streaming sentence-by-sentence synthesis).
*   **HAL:** `pynput` (Keyboard PTT), `sounddevice` (Async Audio I/O).

## Data Pipeline (Asyncio Event Loop)
The application runs as a set of concurrent workers connected via `asyncio.Queue`:

1.  **Audio Capture Task:**
    *   Reads microphone into a Ring Buffer.
    *   VAD monitors for speech. Trigger: Button Release OR silence > 0.5s.
    *   Sends audio segments to `STT_Queue`.

2.  **STT Worker:**
    *   Consumes audio -> Generates source text.
    *   Sends text to `LLM_Queue`.

3.  **LLM Worker (Streaming):**
    *   Consumes text -> Generates translation tokens.
    *   **Accumulator:** Collects tokens into sentences (buffer until punctuation).
    *   Sends complete sentences to `TTS_Queue`.

4.  **TTS Worker (Streaming):**
    *   Consumes sentences -> Generates audio chunks via Piper.
    *   Sends audio to `Playback_Queue`.

5.  **Playback & Interrupts (Barge-in):**
    *   Plays audio from queue.
    *   **Gating:** Playback is blocked while the PTT key is held (configurable).
    *   **Interrupt Logic:** If PTT is pressed during playback -> Current audio stops, queues are cleared, and a new `session_id` is generated.

## Core Mechanisms

### Session Management
Every PTT press increments a `session_id`. All worker tasks (STT, LLM, TTS, Playback) check the `session_id` of the data they are processing. If it doesn't match the current global session ID, the data is discarded immediately. This ensures zero "ghost" translations from previous or cancelled interactions.

### Intelligent Segmentation (Multi-phrase)
The Audio Capture task uses a "harvesting" approach. If a silence period is detected while the PTT key is still held:
1. The current audio buffer is extracted and sent to the pipeline.
2. The pipeline starts processing Part 1 in the background.
3. The recorder continues capturing Part 2.
This allows for near-simultaneous translation of long, thoughtful speech.

### Silent Segment Filtering
To avoid translating background noise or accidental short clicks, the system only sends segments to the STT worker if the VAD (Voice Activity Detection) actually confirmed the presence of speech within that segment.

## Hardware Abstraction Layer (HAL)
*   **InputProvider:** Abstract interface for PTT (Keyboard/GPIO).
*   **AudioIO:** Async wrapper for non-blocking microphone and speaker access.

## Profile Strategy
Defined in `config.yaml`, allowing runtime switching between models (e.g., Qwen 3B for RPi vs. Qwen 14B for Desktop) and hardware backends (CPU/CUDA).
