---
stepsCompleted:
  - step-01-validate-prerequisites
  - step-02-design-epics
  - step-03-create-stories
  - step-04-final-validation
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
  - SCENARIOS.md
---

# offline_translator - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for offline_translator, decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: Users can start a translation session by holding a PTT key.
FR2: The system can transcribe speech to text using the STT engine.
FR3: The system can translate text using the LLM service while preserving context.
FR4: The system can synthesize translated text to speech using the TTS engine.
FR5: The system can process pipeline stages concurrently.
FR6: The system can segment speech automatically during recording via voice activity detection (VAD).
FR7: The system can select the correct language pair based on the active speaker role.
FR8: Users can interrupt audio playback by pressing any PTT key.
FR9: Users can select speaker roles using dedicated keys.
FR10: The system can play translated audio automatically when ready.
FR11: Users can speak up to 10 phrases in one hold session using auto-segmentation.
FR12: The system can manage unique session identifiers to cancel background tasks during interruptions.
FR13: Users can configure language pairs in the system configuration file.
FR14: Users can define model paths in the system configuration file.
FR15: Users can switch between deployment profiles (Desktop/Raspberry Pi).
FR16: Users can tune detection thresholds for segmentation accuracy.
FR17: The system can validate configuration at startup using the configuration validation service.
FR18: The system can capture audio at 16kHz mono float32.
FR19: The system can support various input devices through the hardware abstraction layer.
FR20: The system can operate entirely offline without network dependencies.
FR21: Users can run automated unit and integration tests.
FR22: The system can provide structured error logs for troubleshooting.
FR23: The system can store models and audio data locally only.
FR24: The system can ensure zero data leakage or telemetry collection.

### NonFunctional Requirements

NFR1: Response time ≤ 1.0s from PTT release to audio playback start, measured by internal pipeline timestamps, to ensure natural conversation flow.
NFR2: Segment processing start within 200ms of VAD pause detection, measured by processing logs, to maximize concurrency.
NFR3: CPU usage ≤ 80% on Raspberry Pi 5 hardware, measured by system monitoring tools, to ensure audio stream stability and prevent thermal throttling.
NFR4: Stable operation for 12 continuous hours without restart, measured by soak testing, to support full-day field use.
NFR5: Orchestrator service restoration within 3.0s of failure detection, measured by supervisor logs, to minimize user disruption.
NFR6: Zero pipeline crashes due to single phrase translation errors, measured by error handling tests, to ensure session continuity.
NFR7: Auditory signal latency ≤ 100ms from input trigger, measured by end-to-end latency tests, to provide clear UI status without a screen.
NFR8: Input response latency < 50ms, measured by hardware interrupt logs, to prevent initial audio clipping.
NFR9: Hardware profile switching via configuration change only with zero code modification, measured by configuration audit, to ensure ease of deployment across supported platforms.

### Additional Requirements

**Architecture:**
- **Starter Template:** Custom Python Service-Based Architecture (No frameworks like Typer/Click).
- **Concurrency Model:** Implement "Async First" for I/O/Orchestration and "Thread Isolation" (asyncio.to_thread) for CPU-bound AI services.
- **Hardware Abstraction:** Implement `src/app/core/input.py` with polymorphic `BaseInput` supporting `KeyboardInput` (pynput) and `GPIOInput`.
- **IPC:** Use `asyncio.Queue` and TypedDict payloads (`STTPayload`, `LLMPayload`) for service communication.
- **State Management:** Use `session_id` for cancellation and `asyncio.Event` for state synchronization.
- **Validation:** Use Pydantic-Settings for strict startup validation of model paths and hardware IDs.
- **Model Formats:** Require support for GGUF (LLM), ONNX (TTS), and CTranslate2 (STT).
- **Dependencies:** Use `uv` for package management and `loguru` for structured logging.

**UX/Scenarios:**
- **Segment Harvest:** Implement VAD logic to "harvest" and process segments during 0.5s pauses while the PTT key is still held.
- **Gated Playback:** If `playback_during_recording` is false (default), buffer translated audio and wait for PTT release before playing.
- **Barge-in Logic:** Pressing PTT during playback must immediately stop audio, clear all queues, and cancel the previous session context.
- **Dual PTT Mapping:** Distinct keys (e.g., Space vs Alt) must map to distinct speaker roles and language directions.
- **Headset Mode:** If `playback_during_recording` is true, allow immediate playback of translated segments even while PTT is held.

### FR Coverage Map

FR1: Epic 1 - Start session PTT
FR2: Epic 1 - STT transcription
FR3: Epic 1 - LLM translation
FR4: Epic 1 - TTS synthesis
FR5: Epic 1 - Concurrent pipeline
FR6: Epic 2 - VAD segmentation
FR7: Epic 2 - Language pair selection
FR8: Epic 2 - Barge-in interruption
FR9: Epic 2 - Speaker role keys
FR10: Epic 1 - Auto playback
FR11: Epic 2 - Multi-phrase hold
FR12: Epic 2 - Session IDs
FR13: Epic 3 - Config languages
FR14: Epic 3 - Config models
FR15: Epic 3 - Deployment profiles
FR16: Epic 2 - Tune VAD thresholds
FR17: Epic 3 - Config validation
FR18: Epic 1 - Audio format 16kHz
FR19: Epic 1 - HAL Input abstraction
FR20: Epic 1 - Offline operation
FR21: Epic 3 - Automated tests
FR22: Epic 3 - Error logs
FR23: Epic 1 - Local storage
FR24: Epic 1 - Zero telemetry

## Epic List

### Epic 1: Basic Push-to-Talk Translation (The "Walkie-Talkie" Foundation)
Establish the core offline async pipeline and hardware abstraction layer (HAL) on Windows, enabling users to press a key, speak a single phrase, and hear a translation.
**FRs covered:** FR1, FR2, FR3, FR4, FR5, FR10, FR18, FR19, FR20, FR23, FR24

### Epic 2: Advanced Interaction & Control (The "Conversation" Upgrade)
Enable natural, fluid conversation flows by adding VAD-based auto-segmentation, barge-in interruptions, and multi-speaker role support.
**FRs covered:** FR6, FR7, FR8, FR9, FR11, FR12, FR16

### Epic 3: Configuration & Field Deployment (The "Product" Polish)
Finalize the system for field use by implementing robust configuration management, validation, logging, and deployment profiles for Raspberry Pi.
**FRs covered:** FR13, FR14, FR15, FR17, FR21, FR22

## Epic 1: Basic Push-to-Talk Translation (The "Walkie-Talkie" Foundation)

Establish the core offline async pipeline and hardware abstraction layer (HAL) on Windows, enabling users to press a key, speak a single phrase, and hear a translation.

### Story 1.1: Core Infrastructure & HAL Skeleton

As a Developer,
I want to establish the project structure, configuration system, and hardware abstraction layer (HAL),
So that I can capture audio and input events on Windows without hardcoding platform dependencies.

**Acceptance Criteria:**

**Given** A fresh repository
**When** I run the application
**Then** It should initialize a `ConfigService` that validates `config.yaml` using Pydantic
**And** It should initialize an `InputService` that detects Space/Alt key presses using `pynput` (Windows)
**And** It should initialize an `AudioRecorder` that captures 16kHz mono audio via PortAudio
**And** I can see logs confirming "Input Service Started" and "Audio Recorder Ready" via `loguru`

### Story 1.2: STT Service Integration (Faster-Whisper)

As a Developer,
I want to implement the Speech-to-Text service using Faster-Whisper,
So that I can transcribe recorded audio buffers into text completely offline.

**Acceptance Criteria:**

**Given** A valid path to a quantized Faster-Whisper model in `config.yaml`
**When** I send a float32 audio buffer to `STTService.transcribe()`
**Then** It should return the correct text transcription string
**And** It should execute on a separate thread (via `asyncio.to_thread`) to avoid blocking the main loop
**And** It should raise a typed error if the model fails to load

### Story 1.3: LLM Service Integration (Llama.cpp)

As a Developer,
I want to implement the Translation service using Llama.cpp,
So that I can translate transcribed text from one language to another with context awareness.

**Acceptance Criteria:**

**Given** A valid path to a GGUF model in `config.yaml`
**When** I send a text string and target language to `LLMService.translate()`
**Then** It should return the translated text string
**And** It should maintain a system prompt context that defines the translator's persona
**And** It should run entirely offline without API keys

### Story 1.4: TTS Service Integration (Piper-TTS)

As a Developer,
I want to implement the Text-to-Speech service using Piper-TTS,
So that I can synthesize the translated text into audible speech.

**Acceptance Criteria:**

**Given** A valid path to an ONNX voice model in `config.yaml`
**When** I send a text string to `TTSService.synthesize()`
**Then** It should generate a stream or buffer of audio data
**And** The audio format should match the system output settings (e.g., 16kHz or 22kHz)
**And** It should support switching voices based on the speaker configuration

### Story 1.5: Async Orchestrator & Pipeline Loop

As a User,
I want to press a button, speak, and hear the translation,
So that I can verify the system works end-to-end as a basic translator.

**Acceptance Criteria:**

**Given** The system is running and models are loaded
**When** I hold the defined PTT key, speak a sentence, and release the key
**Then** The system should capture the audio
**And** Pass it through STT -> LLM -> TTS queues sequentially
**And** Play back the translated audio automatically
**And** The total latency from release to playback should be under 2.0 seconds (initial unoptimized target)

## Epic 2: Advanced Interaction & Control (The "Conversation" Upgrade)

Enable natural, fluid conversation flows by adding VAD-based auto-segmentation, barge-in interruptions, and multi-speaker role support.

### Story 2.1: VAD & Auto-Segmentation Logic

As a User,
I want the system to process my speech in segments while I am still holding the button,
So that the translation is ready almost immediately after I finish speaking.

**Acceptance Criteria:**

**Given** I am holding the PTT key and speaking
**When** I pause for more than `vad_threshold` (e.g., 500ms)
**Then** The system should detect the silence using Silero VAD
**And** "Harvest" the current audio buffer and send it to the STT queue immediately
**And** Continue recording the next segment without user intervention

### Story 2.2: Session Management & Cancellation

As a Developer,
I want to track unique session IDs for every interaction,
So that I can surgically cancel stale background tasks without crashing the application.

**Acceptance Criteria:**

**Given** A translation pipeline is active (Session A)
**When** A cancellation event is triggered
**Then** The `SessionManager` should mark Session A as invalid
**And** Any running STT/LLM/TTS tasks checking this `session_id` should abort immediately
**And** The audio output buffer should be cleared

### Story 2.3: Barge-In Interruption Support

As a User,
I want to interrupt the current audio playback by pressing the talk button,
So that I can correct a mistake or reply immediately without waiting for the robot to finish.

**Acceptance Criteria:**

**Given** The system is currently playing audio (TTS output)
**When** I press any PTT key (Space or Alt)
**Then** The audio playback should stop within <50ms
**And** The previous session's remaining queue items should be cancelled
**And** A new recording session should start immediately

### Story 2.4: Dual Speaker Role & Language Switching

As a User,
I want to use different keys for different languages,
So that I can have a bidirectional conversation without manual configuration changes.

**Acceptance Criteria:**

**Given** The config defines Speaker A (En->Ru) on Key 1 and Speaker B (Ru->En) on Key 2
**When** I press Key 1
**Then** The pipeline should use the En->Ru language pair
**When** I press Key 2
**Then** The pipeline should use the Ru->En language pair
**And** The LLM system prompt should adjust to the correct source language context

## Epic 3: Configuration & Field Deployment (The "Product" Polish)

Finalize the system for field use by implementing robust configuration management, validation, logging, and deployment profiles for Raspberry Pi.

### Story 3.1: Raspberry Pi GPIO Implementation

As a Maker,
I want to use physical buttons connected to the Raspberry Pi GPIO pins,
So that I can build a dedicated hardware device without a keyboard.

**Acceptance Criteria:**

**Given** The application is running on a Raspberry Pi (detected via config or OS check)
**When** I configure `input_mode: gpio` in `config.yaml`
**Then** The system should load the `GPIOInput` class instead of `KeyboardInput`
**And** Pressing the physical button connected to the defined PIN should trigger PTT actions
**And** It should handle switch debounce logic to prevent phantom presses

### Story 3.2: Configuration Validation & Profile Switching

As a User,
I want the system to check my configuration and model paths at startup,
So that I don't discover a missing file halfway through a conversation.

**Acceptance Criteria:**

**Given** A `config.yaml` file with invalid model paths
**When** I start the application
**Then** It should exit immediately with a clear, human-readable error message
**And** It should allow switching between "Desktop" and "Pi" profiles via a single config flag

### Story 3.3: Structured Logging & Diagnostics

As a Support Engineer,
I want detailed logs written to a file,
So that I can diagnose why the system failed in the field where there is no screen.

**Acceptance Criteria:**

**Given** The system is running in headless mode
**When** An error occurs (e.g., model crash)
**Then** It should be logged to `logs/app.log` with a timestamp, severity, and stack trace
**And** The log format should be structured (JSON or clear text) for easy parsing

### Story 3.4: Automated Test Suite Integration

As a Developer,
I want to run a single command to verify the entire system,
So that I can be confident my changes didn't break the translation pipeline.

**Acceptance Criteria:**

**Given** I have the repository cloned
**When** I run `uv run pytest`
**Then** It should execute all unit tests for individual services
**And** It should execute integration tests using Mock Inputs and Mock Audio
**And** All 12 critical path tests must pass
