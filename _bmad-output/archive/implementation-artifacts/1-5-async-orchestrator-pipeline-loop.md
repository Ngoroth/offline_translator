# Story 1.5: Async Orchestrator & Pipeline Loop

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a User,
I want to press a button, speak, and hear the translation,
so that I can verify the system works end-to-end as a basic translator.

## Acceptance Criteria

1. **Pipeline Execution**: The system captures audio from the `AudioRecorder`, sends it to `STTService`, then `LLMService`, then `TTSService`, and finally plays it via `AudioPlayer`.
2. **Concurrency**: All services must operate concurrently using `asyncio` queues. STT should be transcribing segment 2 while LLM translates segment 1.
3. **Latency**: Total latency (PTT release to Playback start) should be under 2.0 seconds.
4. **State Management**: Implement a `SessionManager` that tracks the current state (IDLE, LISTENING, PROCESSING, SPEAKING) and `session_id`.
5. **Cancellation**: Releasing the PTT key (in this basic story) or a specific "Stop" event should trigger a cancellation that clears all queues and stops current processing immediately.
6. **Error Handling**: If any service fails, the pipeline should recover gracefully (log error, reset state to IDLE) without crashing.
7. **Type Safety**: Strict `basedpyright` compliance.

## Tasks / Subtasks

- [x] **Define Data Structures**
  - [x] Create `Session` class in `src/app/orchestrator/session.py` with `session_id`, `state`, and `cancel_event`.
  - [x] Define payload TypedDicts in `src/app/core/types.py` (if not existing) or `pipeline.py`: `AudioPayload`, `TextPayload`, `TranslationPayload`.
- [x] **Implement Pipeline Logic** in `src/app/orchestrator/pipeline.py`
  - [x] Create `TranslationPipeline` class.
  - [x] Implement `start_session()` and `stop_session()`.
  - [x] Implement async workers: `_stt_worker`, `_llm_worker`, `_tts_worker`, `_player_worker`.
  - [x] Connect queues: `recorder -> stt_queue -> llm_queue -> tts_queue -> player`.
- [x] **Implement Orchestrator** in `src/app/orchestrator/orchestrator.py` (or `main.py` integration)
  - [x] Coordinate Input events (PTT Press/Release) to Pipeline actions.
  - [x] Handle PTT Release: Stop recording, but keep processing remaining queue items ("drain" mode) until complete or cancelled? *Correction*: Epic 1 is basic PTT. Usually, release = stop recording, start processing.
- [x] **Integration**
  - [x] Wire everything in `src/app/main.py`.
- [x] **Testing**
  - [x] Create `tests/unit/test_orchestrator.py`.
  - [x] Mock all services to test pipeline flow and cancellation.

## Dev Notes

### Critical Implementation Guardrails

- **Async First**: Use `asyncio.Queue` for all data transfer between stages.
- **Worker Pattern**: Each stage (STT, LLM, TTS) should have a dedicated long-running async worker task that consumes from its input queue and pushes to its output queue.
- **Cancellation**:
  - Use `asyncio.Event` for cancellation.
  - Workers should check `if self.session.cancel_event.is_set(): continue/return` before starting heavy work.
  - **Crucial**: When cancelling, drain/clear the queues to prevent stale audio from playing later.
- **State Machine**:
  - `IDLE`: Waiting for input.
  - `LISTENING`: Recording audio.
  - `PROCESSING`: Processing remaining audio (after release).
  - `SPEAKING`: Playing audio.
- **Latency**:
  - Pass generators/iterators where possible?
  - Actually, `STT` yields text segments. `LLM` takes text, yields text. `TTS` takes text, yields audio.
  - Ensure the pipeline supports this streaming flow (1-in, N-out or N-in, M-out).
  - *Note*: STT might output full sentences. LLM streaming is token-by-token but usually we translate sentence-by-sentence for quality.

### Project Structure Notes

- **Orchestrator**: `src/app/orchestrator/`
- **Services**: `src/app/services/` (Already exist)
- **Core**: `src/app/core/`

### References

- [Source: epics.md#Story 1.5]
- [Source: architecture.md#Orchestrator Layer]

## Dev Agent Record

### Agent Model Used

antigravity-gemini-3-pro

### Git Intelligence Summary

- **Existing Code Alert**: A commit "Implement asynchronous streaming pipeline..." exists. **CHECK `src/app/orchestrator/` FIRST.**
- If the code exists, verify it meets the AC and Architecture requirements. Refactor if necessary.
- **Previous Story**: TTS Service (Story 1.4) established the `asyncio.to_thread` pattern. Ensure the Orchestrator doesn't block the loop.

### Latest Technical Information

- **Python 3.12**: Use `asyncio.TaskGroup` for managing the worker tasks if possible (cleaner shutdown/error handling).
- **Loguru**: Ensure context (session_id) is bound to the logger if possible for tracing.

### Completion Notes List

- Defined `Session` class with `SessionState` enum.
- Created `AudioPayload`, `TextPayload`, `TranslationPayload` TypedDicts.
- Fixed existing integration tests to support new type checks and file existence checks.

### File List
src/app/orchestrator/session.py
src/app/core/types.py
src/app/orchestrator/pipeline.py
src/app/orchestrator/orchestrator.py
src/app/main.py
tests/unit/test_session.py
tests/unit/test_types.py
tests/unit/test_orchestrator_pipeline.py
tests/unit/test_orchestrator.py
tests/integration/test_pipeline.py
tests/unit/test_settings.py

### Senior Developer Review (AI)

- **Date**: 2026-01-27
- **Reviewer**: Ngoroth
- **Status**: Approved (with AI Fixes)

#### Findings & Actions
- **Fixed**: Hardcoded Languages. The pipeline now dynamically selects source/target languages based on the PTT role (A/B) and configuration.
- **Fixed**: Role Propagation. The Orchestrator now passes the active role to the pipeline session.
- **Noted**: `src/app/core/config.py` was modified to support these changes but wasn't listed.
- **Noted**: Cleaned up `src/app/core/input_windows.py` and old service files.
