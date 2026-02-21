# Architecture

**Analysis Date:** 2026-02-20

## Pattern Overview

**Overall:** Async Producer-Consumer Pipeline with Event-Driven Coordination

**Key Characteristics:**
- Queue-based worker pattern with sentinel-based termination
- Session-scoped execution with cooperative cancellation
- Hardware Abstraction Layer (HAL) for cross-platform input
- Lazy-loading AI services with async locks

## Layers

**Entry/HAL Layer:**
- Purpose: Application bootstrap and hardware abstraction
- Location: `src/app/main.py`, `src/app/core/input.py`
- Contains: Platform-specific input handlers, device initialization, startup verification
- Depends on: Core layer, Orchestrator layer
- Used by: Direct invocation (`python src/app/main.py`)

**Orchestrator Layer:**
- Purpose: High-level event loop coordination, PTT state management
- Location: `src/app/orchestrator/orchestrator.py`
- Contains: Main loop logic, barge-in handling, press/release coordination
- Depends on: Pipeline layer, HAL layer (BaseInput)
- Used by: Entry layer

**Pipeline Layer:**
- Purpose: Worker task management, queue coordination, session lifecycle
- Location: `src/app/orchestrator/pipeline.py`
- Contains: Worker tasks (_stt_worker, _llm_worker, _tts_worker, _player_worker, _vad_worker), queue definitions
- Depends on: Services layer, Core layer (audio, config), Utils layer (VAD)
- Used by: Orchestrator layer

**Services Layer:**
- Purpose: AI model wrappers with async-safe inference
- Location: `src/app/services/`
- Contains: STTService, LLMService, TTSService - each wrapping a specific AI model
- Depends on: Core layer (config, types), SessionManager (injected)
- Used by: Pipeline layer

**Core Layer:**
- Purpose: Infrastructure, configuration, shared types
- Location: `src/app/core/`
- Contains: Config loading, audio I/O, type definitions, logging setup, startup verification
- Depends on: External libraries only (pydantic, sounddevice, loguru)
- Used by: All other layers

**Utils Layer:**
- Purpose: Shared utilities and algorithms
- Location: `src/app/utils/`
- Contains: VADService, SilenceDetector, AudioRingBuffer
- Depends on: Core layer (minimal), external libraries (webrtcvad, numpy)
- Used by: Pipeline layer, Core audio

## Data Flow

**Translation Pipeline (Normal Flow):**

1. User presses PTT button (Role A or B)
2. Orchestrator receives press event via `input.wait_for_press()`
3. Pipeline starts session: `pipeline.start_session(role)` - creates Session, starts recorder and workers
4. User speaks into microphone - audio flows through recorder callback into ring buffer
5. User releases PTT button
6. Orchestrator calls `pipeline.handle_input_complete()`:
   - Stops recorder, retrieves audio buffer
   - Creates AudioPayload, pushes to `stt_queue`
   - Sends sentinel (None) to signal end
7. STT Worker consumes from `stt_queue`, transcribes, pushes TextPayload to `llm_queue`
8. LLM Worker consumes from `llm_queue`, translates, pushes TranslationPayload to `tts_queue`
9. TTS Worker consumes from `tts_queue`, synthesizes audio, pushes bytes to `player_queue`
10. Player Worker consumes from `player_queue`, plays audio through speakers
11. All workers exit on sentinel, `wait_for_completion()` returns
12. Orchestrator loops back to waiting for next press

**Barge-In Flow:**

1. User presses PTT while pipeline is still processing/speaking
2. Orchestrator detects via `asyncio.wait()` with FIRST_COMPLETED
3. Cancels completion wait, calls `pipeline.handle_barge_in()`
4. Pipeline stops session: sets cancel_event, stops player, stops recorder, cancels workers, clears queues
5. New session starts immediately with pressed role

**VAD Auto-Harvest Flow (when enabled):**

1. VAD Worker continuously monitors audio chunks from recorder
2. When silence threshold reached, extracts buffer via `recorder.extract_buffer()`
3. Pushes audio segment to `stt_queue` while user is still holding PTT
4. Enables multiple phrases per PTT hold session

**State Management:**
- Session object tracks: session_id, state (IDLE/LISTENING/PROCESSING/SPEAKING), source_lang, target_lang, tts_voice
- SessionManager tracks active sessions, enables cooperative cancellation
- asyncio.Event used for cancel signalling across services

## Key Abstractions

**BaseInput (Abstract Class):**
- Purpose: Hardware abstraction for PTT input
- Examples: `src/app/core/input.py` (KeyboardInput, EvdevInput, GPIOInput)
- Pattern: Strategy/HAL - different implementations selected at runtime via factory
- Methods: `wait_for_press()`, `wait_for_release(role)`, `is_pressed(role)`, `start()`, `stop()`

**Session (Dataclass):**
- Purpose: Encapsulates translation session state
- Examples: `src/app/orchestrator/session.py`
- Pattern: Value object with cancellation support
- Fields: session_id, state, cancel_event, source_lang, target_lang, tts_voice

**Payload TypedDicts:**
- Purpose: Type-safe data transfer objects between pipeline stages
- Examples: `src/app/core/types.py` (AudioPayload, TextPayload, TranslationPayload)
- Pattern: Data Transfer Object (DTO) with explicit typing

**Service Classes:**
- Purpose: Wrapper around AI models with async interface
- Examples: `src/app/services/stt.py`, `src/app/services/llm.py`, `src/app/services/tts.py`
- Pattern: Facade - hides blocking model calls behind async methods
- Common traits: lazy model loading, session cancellation checks, async locks

## Entry Points

**Main Application:**
- Location: `src/app/main.py`
- Triggers: `python src/app/main.py` or `uv run python src/app/main.py`
- Responsibilities:
  1. Setup logging
  2. Load configuration from YAML
  3. Verify startup prerequisites (models, audio devices)
  4. Resolve and validate audio devices
  5. Initialize hardware (input handler, recorder, player)
  6. Initialize AI services (STT, LLM, TTS)
  7. Create pipeline and orchestrator
  8. Run orchestrator event loop

**Model Download Script:**
- Location: `scripts/download_models.py`
- Triggers: `uv run python scripts/download_models.py`
- Responsibilities: Downloads LLM (Qwen) and TTS (Piper) models from HuggingFace

**Hardware Diagnostics:**
- Location: `scripts/hardware_check.py`, `scripts/diagnose.py`
- Triggers: Manual invocation for debugging
- Responsibilities: Verify audio devices, test recording

## Error Handling

**Strategy:** Fail-fast at startup, graceful degradation at runtime

**Patterns:**
- Custom exceptions with actionable suggestions: `AudioDeviceError` in `src/app/core/audio/recorder.py`
- Service-specific exceptions: `STTError`, `STTModelLoadError`, `STTTranscriptionError` in services
- Session cancellation checks: All services check `session_manager.is_valid()` before/after blocking operations
- Worker exception isolation: Each worker catches exceptions, logs, and continues or exits

**Error Propagation:**
- Startup errors exit with specific codes (1: models, 2: audio devices)
- Runtime errors logged and session cancelled
- Unhandled exceptions in main() caught and logged with full traceback

## Cross-Cutting Concerns

**Logging:** 
- Framework: loguru
- Setup: `src/app/core/logging.py` - console (formatted) + file (JSON)
- Pattern: Structured logging with context, file rotation at 10MB

**Validation:**
- Config: Pydantic models with field validators in `src/app/core/config.py`
- Audio: Device resolution with fallbacks in `src/app/core/audio/devices.py`

**Configuration:**
- Format: YAML with profile selection
- Loading: `load_settings()` in `src/app/core/config.py`
- Hierarchy: RootConfig (profile selection) -> AppSettings (validated profile)
- Environment overrides: Supports `APP_*` environment variables via pydantic-settings

**Async Patterns:**
- `asyncio.to_thread()` for blocking I/O (model inference, audio I/O)
- `asyncio.Queue` for inter-worker communication
- `asyncio.Lock` for serializing model access
- `asyncio.Event` for cancellation signalling
- `asyncio.wait()` with FIRST_COMPLETED for barge-in detection

**Threading:**
- Audio recorder uses separate thread for stdout reading
- GPIO callbacks run in separate thread, use `call_soon_threadsafe` for async coordination
- Audio player uses blocking `sd.play()` with lock-protected state

---

*Architecture analysis: 2026-02-20*
