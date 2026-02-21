# Product Requirements Document - offline_translator

**Author:** Ngoroth
**Date:** 2026-02-09

## Executive Summary

Offline Translator (Neuromancer Pi) is a high-performance, privacy-first speech-to-speech translation system designed for real-time bilingual communication in environments without internet access. The system features an innovative async pipeline architecture that enables concurrent processing of audio, text, and speech for near-zero latency. By processing speech segments while the user is still speaking (auto-segmentation), the system delivers translations almost instantly after the button is released.

Unlike traditional translation apps that force users to wait through sequential processing after speaking, this solution leverages stream-based async pipelines to minimize delay. The system is designed with a hardware abstraction layer to support multiple platforms, including Windows desktops and Raspberry Pi 4, making it ideal for outdoor activities like hiking and camping where internet connectivity is unavailable.

## Success Criteria

### Business Success
- **Community Adoption**: At least one user beyond the author successfully uses the application.
- **Public Availability**: Code is available on GitHub with comprehensive README and setup instructions.
- **Extensibility**: Other users can successfully configure their own language pairs via configuration.

### Technical Success
- **Near-Zero Latency**: Translation is ready ≤ 1.0 second after PTT button release.
- **Smooth Playback**: Minimal delay between translation readiness and audio playback (target range: 0.3-1.0s).
- **Session Stability**: Reliable support for one simultaneous session (one dialogue pair).
- **Test Integrity**: 100% pass rate for the minimum 12 critical tests (unit and integration), aiming for maximum coverage.

## Domain-Specific Requirements

### Technical Constraints
- **Offline Inference**: All AI models (STT, LLM, TTS) must be quantized for local execution.
- **Audio Standards**: Real-time processing at 16kHz mono float32.
- **Concurrent Processing**: Hard requirement for parallel pipeline stages to meet latency goals.

### Privacy & Data
- **Zero Telemetry**: No data collection or external reporting.
- **Data Locality**: All audio and text buffers must remain on-device.

### Risk Mitigations
- **Translation Quality**: Use modern LLMs with prompt engineering to preserve idioms.
- **Hardware Limitations**: Mitigate Raspberry Pi 4 CPU constraints by using smaller models and optimized VAD.

## Assumptions & Dependencies

### Hardware
- **Compute**: Raspberry Pi 4 Model B (2GB RAM).
- **Audio Input**: USB Analog Microphone (Plug-and-Play class compliant).
- **Control**: USB Numeric Keypad (Numpad) for PTT control.
- **Audio Output**: 3.5mm Jack or USB Audio output.

### Environment
- **Noise Level**: Performance is optimized for low-to-moderate ambient noise. High noise environments may degrade STT accuracy.
- **Power**: Stable 5V 3A power supply required for RPi4 and USB peripherals.

### Software/Data
- **Models**: Quantized models (GGUF/ONNX) must fit within available RAM (leaving ~256MB for OS/System).

## Innovation & Novel Patterns


## Desktop/CLI/Embedded Specific Requirements

### Technical Architecture Considerations
- **Platform Support**: Primary support for Windows and Raspberry Pi 4.
- **System Integration**: Cross-platform audio I/O, hardware abstraction for input devices.
- **Manual Updates**: Users pull code and download models manually via the repository or provided scripts.

### Model Management
- **Manual Control**: Models are downloaded via utility scripts and stored in a local directory.
- **Validation**: System must validate model paths and files during initialization.

### Configuration Schema
| Parameter | Description | Example Value |
| :--- | :--- | :--- |
| `stt_model_path` | Path to the STT model file | `./models/stt.bin` |
| `llm_model_path` | Path to the quantized LLM file | `./models/llm_v1.bin` |
| `tts_model_path` | Path to the TTS voice model | `./models/voice_v1.bin` |
| `vad_threshold` | Sensitivity for voice detection | `0.5` |
| `input_device_id` | System ID for microphone | `1` |
| `output_device_id`| System ID for speakers | `0` |
| `speaker_a_lang` | Language code for speaker A | `ru` |
| `speaker_b_lang` | Language code for speaker B | `en` |

## Functional Requirements

### Translation & Speech Processing
- **FR1**: Users can start a translation session by holding a PTT key.
- **FR2**: The system can transcribe speech to text using the STT engine.
- **FR3**: The system can translate text while preserving context.
- **FR4**: The system can synthesize translated text to speech.
- **FR5**: The system can process pipeline stages concurrently.
- **FR6**: The system can segment speech automatically during recording.
- **FR7**: The system can select the correct language pair based on the active speaker role.

### Interaction & UI
- **FR8**: Users can interrupt audio playback by pressing any PTT key.
- **FR9**: Users can select speaker roles using dedicated keys.
- **FR10**: The system can play translated audio automatically when ready.
- **FR11**: Users can speak up to 10 phrases in one hold session using auto-segmentation.
- **FR12**: The system can cancel background tasks during interruptions.

### Configuration & Platform
- **FR13**: Users can configure language pairs in the system configuration file.
- **FR14**: Users can define model paths in the system configuration file.
- **FR15**: Users can switch between deployment profiles (Desktop/Raspberry Pi).
- **FR16**: Users can tune detection thresholds for segmentation accuracy.
- **FR17**: The system can validate configuration at startup using the configuration validation service.
- **FR18**: The system can capture audio at 16kHz mono float32.
- **FR19**: The system can support USB input devices (Numpad, Microphone) through the hardware abstraction layer.
- **FR20**: The system can operate entirely offline without network dependencies.

### Testing & Privacy
- **FR21**: Users can run automated unit and integration tests.
- **FR22**: The system can provide structured error logs for troubleshooting.
- **FR23**: The system can store models and audio data locally only.
- **FR24**: The system can ensure zero data leakage or telemetry collection.

## Non-Functional Requirements

### Performance
- **NFR1 (Latency)**: Response time ≤ 1.0s from PTT release to audio playback start, measured by internal pipeline timestamps, to ensure natural conversation flow.
- **NFR2 (Streaming)**: Segment processing start within 200ms of VAD pause detection, measured by processing logs, to maximize concurrency.
- **NFR3 (Resources)**: CPU usage ≤ 80% on Raspberry Pi 4 hardware, measured by system monitoring tools, to ensure audio stream stability and prevent thermal throttling.

### Reliability & Usability
- **NFR4 (Autonomy)**: Stable operation for 12 continuous hours without restart, measured by soak testing, to support full-day field use.
- **NFR5 (Recovery)**: Orchestrator service restoration within 3.0s of failure detection, measured by supervisor logs, to minimize user disruption.
- **NFR6 (Integrity)**: Zero pipeline crashes due to single phrase translation errors, measured by error handling tests, to ensure session continuity.
- **NFR7 (Feedback)**: Auditory signal latency ≤ 100ms from input trigger, measured by end-to-end latency tests, to provide clear UI status without a screen.
- **NFR8 (Tactility)**: Input response latency < 50ms, measured by hardware interrupt logs, to prevent initial audio clipping.

### Portability
- **NFR9 (HAL)**: Hardware profile switching via configuration change only with zero code modification, measured by configuration audit, to ensure ease of deployment across supported platforms.

## Glossary

- **PTT (Push-to-Talk)**: A method of conversation where the user holds a button to speak and releases it to send the audio.
- **STT (Speech-to-Text)**: The process of converting spoken audio into text.
- **TTS (Text-to-Speech)**: The process of converting text into spoken audio.
- **LLM (Large Language Model)**: The AI component responsible for translation and context handling.
- **HAL (Hardware Abstraction Layer)**: A software layer that allows the application to interact with different hardware (Windows vs. RPi) uniformly.
- **Barge-in**: The ability to interrupt the current audio playback by pressing a PTT key.
