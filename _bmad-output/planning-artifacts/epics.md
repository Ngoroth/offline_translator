---
stepsCompleted: ["step-01-validate-prerequisites", "step-02-design-epics", "step-03-create-stories"]
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
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

NFR1 (Latency): Response time ≤ 1.0s from PTT release to audio playback start.
NFR2 (Streaming): Segment processing start within 200ms of VAD pause detection.
NFR3 (Resources): CPU usage ≤ 80% on Raspberry Pi 5 hardware (Note: User targeting RPi 4).
NFR4 (Autonomy): Stable operation for 12 continuous hours without restart.
NFR5 (Recovery): Orchestrator service restoration within 3.0s of failure detection.
NFR6 (Integrity): Zero pipeline crashes due to single phrase translation errors.
NFR7 (Feedback): Auditory signal latency ≤ 100ms from input trigger.
NFR8 (Tactility): Input response latency < 50ms.
NFR9 (HAL): Hardware profile switching via configuration change only with zero code modification.

### Additional Requirements

- **Target Platform**: Raspberry Pi 4 (Explicit user request overrides PRD's RPi 5 target).
- **HAL Implementation**: Must implement GPIO input support for RPi 4.
- **Architecture Starter**: Custom Python Service-Based Architecture (Asyncio + ThreadPools).
- **Audio I/O**: PortAudio dependency for cross-platform low-latency audio.
- **Concurrency**: Asyncio for I/O and orchestration; ThreadPools for CPU-bound AI inference.
- **Configuration**: Pydantic-Settings for strict validation.
- **Storage**: No DB. File-based configuration and models.
- **Deployment**: Manual git pull and script execution.

### FR Coverage Map

FR1: Epic 1 - Start session PTT
FR2: Epic 1 - STT transcription
FR3: Epic 1 - LLM translation
FR4: Epic 1 - TTS synthesis
FR5: Epic 1 - Concurrent pipeline
FR6: Epic 1 - VAD segmentation
FR7: Epic 1 - Language pair selection
FR8: Epic 1 - Barge-in interruption
FR9: Epic 1 - Speaker role keys
FR10: Epic 1 - Auto playback
FR11: Epic 1 - Multi-phrase hold
FR12: Epic 1 - Session IDs
FR13: Epic 1 - Config languages
FR14: Epic 1 - Config models
FR15: Epic 1 - Deployment profiles
FR16: Epic 1 - Tune VAD thresholds
FR17: Epic 1 - Config validation
FR18: Epic 1 - Audio format 16kHz
FR19: Epic 1 - HAL Input abstraction
FR20: Epic 1 - Offline operation
FR21: Epic 1 - Automated tests
FR22: Epic 1 - Error logs
FR23: Epic 1 - Local storage
FR24: Epic 1 - Zero telemetry

## Epic List

### Epic 1: Raspberry Pi 4 Deployment & Core Functionality
Deploy the existing Windows-verified application to Raspberry Pi 4, ensuring all translation, interaction, and configuration features function correctly on the target hardware with USB Numpad support.
**FRs covered:** FR1, FR2, FR3, FR4, FR5, FR6, FR7, FR8, FR9, FR10, FR11, FR12, FR13, FR14, FR15, FR16, FR17, FR18, FR19, FR20, FR21, FR22, FR23, FR24

## Epic 1: Raspberry Pi 4 Deployment & Core Functionality

Deploy the existing Windows-verified application to Raspberry Pi 4, ensuring all translation, interaction, and configuration features function correctly on the target hardware with USB Numpad support.

### Story 1.1: Core Deployment & Service Verification

As a Developer,
I want to deploy and verify the application on Raspberry Pi 4,
So that I can confirm the core pipeline works on the target hardware.

**Acceptance Criteria:**

**Given** A fresh Raspberry Pi 4 installation (Raspberry Pi OS Bookworm)
**When** I clone the repository and run `uv sync`
**Then** All dependencies should install successfully
**When** I run `uv run python src/app/main.py`
**Then** The application should start without crashing (even if models/audio are not configured yet)
**And** Logs should show successful service initialization

### Story 1.2: USB Numpad Input Implementation

As a User,
I want to use a USB Numpad to trigger translation and switch roles,
So that I can control the device easily in the field using a robust input device.

**Acceptance Criteria:**

**Given** A USB Numpad connected to the Raspberry Pi
**When** I configure `input_device_type: keyboard` in `config.yaml`
**And** I press the assigned PTT key (e.g., Numpad Enter or Numpad 0)
**Then** The system should log "PTT Press Detected"
**And** I should be able to map different keys to different languages/roles
**Note**: Must ensure input works in the specific RPi runtime environment (Headless vs Desktop, potentially using `evdev` if `pynput` fails in headless).

### Story 1.3: Audio I/O Configuration

As a User,
I want the system to use the correct microphone and speaker on the RPi,
So that I can be heard and hear translations clearly.

**Acceptance Criteria:**

**Given** A USB microphone/speaker or HAT connected
**When** I list audio devices via `scripts/list_audio_devices.py` (if available) or `arecord -l`
**And** I configure the device IDs in `config.yaml`
**Then** The application should capture audio without errors
**And** The application should play back synthesized speech clearly through the selected output

### Story 1.4: Performance Tuning for RPi 4

As a Developer,
I want to optimize the models and pipeline for Raspberry Pi 4 constraints,
So that latency is minimized (<2s acceptable, <1s target) and CPU usage is stable.

**Acceptance Criteria:**

**Given** The application is running on RPi 4
**When** I perform a translation cycle
**Then** CPU usage should not exceed 90% (monitor via `htop`)
**And** Latency should be measured and logged
**If** Latency is >2s, consider switching to smaller models (e.g., `tiny.en` for Whisper, `q4_k_m` for Llama)
**And** Confirm memory usage fits within available RAM (leaving room for OS)

### Story 1.5: End-to-End Field Validation

As a User,
I want to use the device as a "Walkie-Talkie" translator,
So that I can have a bilingual conversation in the field.

**Acceptance Criteria:**

**Given** The fully configured device
**When** I hold PTT, speak a phrase, and release
**Then** The system should translate and speak the result correctly
**When** I switch roles/languages via GPIO buttons (if implemented) or config
**Then** It should translate in the other direction
**And** The system should remain stable for >10 minutes of usage
