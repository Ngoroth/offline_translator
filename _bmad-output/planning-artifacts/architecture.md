---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/product-brief-offline_translator-2026-01-21.md
  - docs/index.md
  - docs/project-overview.md
  - docs/architecture.md
  - docs/development-guide.md
  - docs/source-tree-analysis.md
workflowType: 'architecture'
project_name: 'offline_translator'
user_name: 'Ngoroth'
date: '2026-01-22'
lastStep: 8
status: 'complete'
completedAt: '2026-01-22'
---

# Architecture Decision Document

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**
The system is built around 24 functional requirements focused on seamless bidirectional speech-to-speech translation. Architecturally, this necessitates an asynchronous orchestrator that manages the lifecycle of three concurrent AI services (STT, LLM, TTS). The presence of a PTT interface with barge-in support requires a robust cancellation mechanism (cancellation tokens/session IDs).

**Non-Functional Requirements:**
- **Latency (NFR1)**: ≤ 1.0s — Primary driver, requiring stream-based processing.
- **Resource Efficiency (NFR3)**: ≤ 80% CPU on RPi 5 — Limits model selection (quantized only) and sampling rate (16kHz).
- **Reliability (NFR5)**: Auto-recovery of services within 3s — Requires service health monitoring.
- **Tactility (NFR8)**: Input response latency < 50ms — Requires optimized HAL.

**Scale & Complexity:**
- Primary domain: Desktop / Embedded / Edge AI
- Complexity level: Medium (High focus on concurrency and timing)
- Estimated architectural components: ~8 (Orchestrator, Session Manager, STT, LLM, TTS, HAL, Audio, Config)

### Technical Constraints & Dependencies
- **Offline Only**: Zero external network dependencies.
- **Quantized Models**: Mandatory use of GGUF (LLM) and ONNX (TTS) formats.
- **PortAudio**: Dependency for cross-platform low-latency audio I/O.
- **Hardware Abstraction**: Strict separation of Windows (pynput) and RPi (GPIO) logic.

### Cross-Cutting Concerns Identified
- **Session Management**: Handling `session_id` for correct barge-in behavior.
- **Configuration Validation**: Strict startup validation of model paths and hardware IDs.
- **Structured Error Logging**: Diagnosis in headless environments via `loguru`.

## Starter Template Evaluation

### Primary Technology Domain
Desktop / Embedded / Edge AI based on Python 3.12.

### Starter Options Considered
1. **Standard CLI (Typer/Click)**: Rejected. Insufficient for complex async lifecycle management and concurrent processing.
2. **Service-Oriented Custom Structure**: Selected. Focuses on isolation of AI engines and hardware abstraction without framework overhead.

### Selected Starter: Custom Python Service-Based Architecture
**Rationale for Selection:**
The project requires high control over thread/process isolation for AI models and strict timing for audio I/O. A custom structure following clean architecture principles is superior to generic templates for minimizing latency on embedded hardware.

**Architectural Decisions Provided:**
- **Language**: Python 3.12 (UV managed).
- **Concurrency**: Asyncio for I/O and orchestration; ThreadPools for CPU-bound AI inference.
- **Config**: Pydantic-Settings for strict validation of model paths and hardware IDs.
- **HAL**: Base class interface for all platform-specific I/O.

## Core Architectural Decisions

### Decision Priority Analysis
**Critical Decisions:**
- **Concurrency Model**: Asyncio + ThreadPoolExecutor (to isolate blocking C++ calls).
- **HAL Strategy**: Polymorphic `BaseInput` -> `GPIOInput`/`KeyboardInput`.
- **State Machine**: Custom implementation using Python 3.10+ `match/case` and `asyncio.Event`.
- **Barge-in Mechanism**: Global Cancellation Event + Queue Flushing.

### Data Architecture
- **Storage**: No DB. File-based configuration (`config.yaml`) and models (`models/`).
- **Validation**: Pydantic for configuration schema validation at startup.

### API & Communication Patterns
- **Internal IPC**: `asyncio.Queue` for data pipelines between services (STT -> LLM -> TTS).
- **Protocols**: TypedDict payloads (`STTPayload`, `LLMPayload`, `TTSPayload`).

### Infrastructure & Deployment
- **Runtime**: Python 3.12 (managed by `uv`).
- **Target Hardware**: Raspberry Pi 5 (Arm64) / Windows Dev.
- **Model Format**: GGUF (LLM), ONNX (TTS), CTranslate2 (STT).

## Implementation Patterns & Consistency Rules

### Code Naming Conventions
- **Classes**: PascalCase (`AudioRecorder`, `TranslatorService`).
- **Functions/Variables**: snake_case (`start_recording`, `session_id`).
- **Constants**: UPPER_CASE (`SAMPLE_RATE`, `VAD_FRAME_MS`).
- **Private Members**: Prefix `_` (`_buffer`, `_stream`).

### Concurrency Patterns
- **Async First**: All I/O code (files, queues, events) must be async.
- **Thread Isolation**: CPU-bound tasks (STT/LLM/TTS inference) MUST be wrapped in `asyncio.to_thread`.
- **Cancellation**: Long-running loops must check `if cancel_event.is_set(): return` frequently.

### Structure Patterns
- **Dependency Injection**: Services receive dependencies (config, queues) in `__init__`.
- **Configuration**: Access only via `app.settings.load_settings()`.
- **HAL Usage**: Never import `pynput` or `RPi.GPIO` in business logic; use `core.input` abstraction.

### Error Handling
- **Logging**: Use `loguru`.
  - `info`: State transitions.
  - `debug`: Stream chunk details.
  - `error`: Exceptions with context.
- **Resilience**: Workers should catch exceptions inside their loop to prevent pipeline crash.

## Project Structure & Boundaries

### Complete Project Directory Structure
```text
offline_translator/
├── pyproject.toml          # Dependencies (uv)
├── README.md               # Setup & Usage
├── config.yaml             # Runtime Configuration
├── .gitignore              # Models & Logs exclusion
├── scripts/
│   └── download_models.py  # Model Downloader (with SHA256 check)
├── tests/
│   ├── integration/        # End-to-End Pipeline Tests
│   ├── unit/               # Service Logic Tests
│   └── mocks/              # MockInput, MockAudioRecorder
├── src/
│   └── app/
│       ├── __init__.py
│       ├── main.py         # DI Container & Entry Point
│       ├── core/           # Infrastructure Layer
│       │   ├── audio/      # Audio I/O
│       │   │   ├── recorder.py
│       │   │   └── player.py
│       │   ├── config.py   # Pydantic Settings
│       │   ├── logging.py  # Loguru Config
│       │   └── input.py    # HAL (BaseInput, KeyboardInput, GPIOInput)
│       ├── services/       # AI Layer (Concrete Wrappers)
│       │   ├── stt.py      # Faster-Whisper
│       │   ├── llm.py      # Llama.cpp
│       │   └── tts.py      # Piper-TTS
│       ├── orchestrator/   # Application Layer
│       │   ├── session.py  # State Machine & Lifecycle
│       │   └── pipeline.py # Async Workers & Queues
│       └── utils/          # Helpers
│           ├── vad.py      # Voice Activity Detection
│           └── buffers.py  # Ring Buffers
```

### Architectural Boundaries
- **Hardware Layer**: `src/app/core/input.py` is the ONLY place where platform-specific input libraries exist.
- **AI Layer**: `src/app/services/*` encapsulates all ML model interactions.
- **Orchestration Layer**: `src/app/orchestrator/*` manages the flow and state, unaware of specific model implementations.

### Requirements Mapping
- **Async Pipeline**: `src/app/orchestrator/pipeline.py`
- **State Machine**: `src/app/orchestrator/session.py`
- **HAL**: `src/app/core/input.py`
- **Config Schema**: `src/app/core/config.py`

## Architecture Validation Results

### Coherence Validation ✅
**Decision Compatibility:**
Stack (Python 3.12/Asyncio/UV) is verified compatible with Raspberry Pi 5 / Arm64.
**Pattern Consistency:**
Async-first approach applied consistently across I/O, AI integration, and State Management.

### Requirements Coverage Validation ✅
**Functional Requirements:**
- All AI services mapped to isolated modules in `services/`.
- Barge-in mapped to cancellation logic in `orchestrator/`.
- Config validation mapped to `core/config.py`.

**Non-Functional Requirements:**
- **Latency**: Optimization via stream processing and VAD chunking.
- **Reliability**: Service isolation and error handling patterns defined.
- **Testability**: Mocks defined for HAL to enable CI/CD testing.

### Implementation Readiness Validation ✅
**Decision Completeness:**
Critical decisions (HAL, State Machine, Concurrency) are fully documented.
**Gap Analysis:**
- **Addressed**: Explicit requirement for `tests/mocks/` added.
- **Addressed**: `download_models.py` robustness (SHA256) added.

**Architecture Readiness Assessment**
**Overall Status:** READY FOR IMPLEMENTATION
**Confidence Level:** High
