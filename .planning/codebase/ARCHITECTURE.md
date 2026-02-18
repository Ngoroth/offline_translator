# Architecture

**Analysis Date:** 2025-02-17

## Pattern Overview

**Overall:** Async Pipeline with Hardware Abstraction Layer

**Key Characteristics:**
- **Asyncio-based**: Full async/await concurrency model for non-blocking I/O
- **Producer-Consumer Pipeline**: 4-stage async queue pipeline (VAD → STT → LLM → TTS → Audio)
- **Hardware Abstraction**: Platform-independent input (Keyboard/Evdev/GPIO) and audio (ALSA/PortAudio)
- **Session-based State Management**: Cancellable sessions for barge-in support
- **Cross-platform**: Windows development, Raspberry Pi production deployment

## Layers

**Application Layer:**
- Purpose: Entry point, dependency injection, configuration loading
- Location: `src/app/main.py`
- Contains: Main loop, service initialization, HAL factory
- Depends on: All other layers
- Used by: None (entry point)

**Orchestration Layer:**
- Purpose: Coordinates pipeline lifecycle and input handling
- Location: `src/app/orchestrator/`
- Contains: `Orchestrator`, `TranslationPipeline`, `Session`, `SessionManager`
- Depends on: Services, Core
- Used by: Application Layer

**Services Layer:**
- Purpose: AI model wrappers (STT, LLM, TTS)
- Location: `src/app/services/`
- Contains: `STTService`, `LLMService`, `TTSService`
- Depends on: Core (settings), Orchestrator (sessions)
- Used by: Orchestration Layer

**Core Layer:**
- Purpose: Hardware abstraction and configuration
- Location: `src/app/core/`
- Contains: Audio I/O, Input devices, Config, Types
- Depends on: Utils
- Used by: All other layers

**Utils Layer:**
- Purpose: Supporting utilities
- Location: `src/app/utils/`
- Contains: `AudioRingBuffer`, `VADService`, `SilenceDetector`
- Depends on: None
- Used by: Core, Services

## Data Flow

**Translation Pipeline:**

1. **Input Trigger**: User presses PTT button (Keyboard/GPIO/Evdev)
2. **Session Start**: `TranslationPipeline.start_session()` creates session, determines source/target languages
3. **Audio Capture**: `AudioRecorder` captures via arecord (Pi) or sounddevice (Windows)
4. **VAD Processing**: `VADService` + `SilenceDetector` monitor for speech/silence
5. **STT Worker**: Audio chunks queued to `_stt_worker()` → `STTService.transcribe()`
6. **LLM Worker**: Text queued to `_llm_worker()` → `LLMService.translate()`
7. **TTS Worker**: Translated text queued to `_tts_worker()` → `TTSService.synthesize()`
8. **Playback**: Audio chunks queued to `_player_worker()` → `AudioPlayer.play()`
9. **Completion/Interrupt**: On PTT release, sentinels flush pipeline. On barge-in, cancel event stops all.

**State Management:**
- Session state: `IDLE → LISTENING → PROCESSING → SPEAKING → IDLE`
- Cancellation via `Session.cancel_event` and `SessionManager` validity checks
- Cooperative cancellation at service boundaries

## Key Abstractions

**BaseInput (Hardware Abstraction):**
- Purpose: Abstract input device interface
- File: `src/app/core/input.py`
- Pattern: Abstract Base Class with concrete implementations
- Implementations: `KeyboardInput` (pynput), `EvdevInput` (evdev), `GPIOInput` (lgpio)

**Session:**
- Purpose: Encapsulate translation transaction state
- File: `src/app/orchestrator/session.py`
- Pattern: Dataclass with lifecycle management
- Fields: `session_id`, `state`, `cancel_event`, `source_lang`, `target_lang`, `tts_voice`

**Typed Payloads:**
- Purpose: Type-safe queue communication
- File: `src/app/core/types.py`
- Pattern: TypedDict for pipeline stage handoff
- Types: `AudioPayload`, `TextPayload`, `TranslationPayload`

**Service Pattern:**
- Purpose: Wrap blocking ML models in async interface
- Files: `src/app/services/*.py`
- Pattern: Async facade with lazy initialization, thread offloading
- Features: Session-aware cancellation, locking for model access

## Entry Points

**Main Entry Point:**
- Location: `src/app/main.py`
- Triggers: Direct execution: `python -m app.main` or `uv run python src/app/main.py`
- Responsibilities:
  1. Setup logging (`setup_logging()`)
  2. Load configuration (`load_settings()`)
  3. Initialize input handler (HAL factory)
  4. Initialize audio (recorder/player)
  5. Initialize AI services (STT, LLM, TTS)
  6. Create pipeline and orchestrator
  7. Run main loop (`await orchestrator.run()`)

**Test Entry Points:**
- Unit: `tests/unit/test_*.py` - pytest
- Smoke: `tests/smoke/` - Initialization and wiring tests
- E2E: `tests/e2e/` - Full pipeline with real models

## Error Handling

**Strategy:** Layered exception handling with logging

**Patterns:**
- Service exceptions: Custom exception hierarchies (`STTError`, `LLMError`)
- Cancellation: `asyncio.CancelledError` for graceful shutdown, `Session.cancel_event` for barge-in
- Configuration: Pydantic validation with descriptive errors
- Hardware: Graceful degradation (e.g., fallback input modes)

**Critical Paths:**
- Audio capture failures logged, may raise to main
- Model load failures raise at startup
- Pipeline stage failures logged, continue processing (don't crash pipeline)

## Cross-Cutting Concerns

**Logging:**
- Framework: loguru
- Setup: `src/app/core/logging.py`
- Pattern: Structured JSON logging to file, formatted console output
- Configuration: 10MB rotation, 1 week retention

**Configuration:**
- Framework: Pydantic Settings with YAML file
- File: `src/app/core/config.py`
- Pattern: Profile-based config in `config.yaml`, env var override support
- Validation: File existence, key uniqueness, path validation

**Validation:**
- Framework: Pydantic model validators
- Location: Inline in config models
- Pattern: `@model_validator`, `@field_validator` decorators

---

*Architecture analysis: 2025-02-17*
