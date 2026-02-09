# Story 2.2: Session Management & Cancellation

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Developer,
I want to track unique session IDs for every interaction,
so that I can surgically cancel stale background tasks without crashing the application.

## Acceptance Criteria

1.  **Given** A translation pipeline is active (Session A)
2.  **When** A cancellation event is triggered (e.g., barge-in)
3.  **Then** The `SessionManager` should mark Session A as invalid
4.  **And** Any running STT/LLM/TTS tasks checking this `session_id` should abort immediately
5.  **And** The audio output buffer should be cleared
6.  **And** A new session ID should be generated for the next interaction

## Tasks / Subtasks

- [x] **Implement `SessionManager`**
    - [x] Create `src/app/orchestrator/session.py`.
    - [x] Implement `start_session() -> str` (generate UUID).
    - [x] Implement `cancel_session(session_id)`.
    - [x] Implement `is_valid(session_id) -> bool`.
    - [x] use `asyncio.Event` for global cancellation signaling if needed, but prefer ID checks for surgical precision.
- [x] **Update Pipeline Payloads**
    - [x] Add `session_id: str` to `STTPayload`, `LLMPayload`, `TTSPayload` in `src/app/orchestrator/pipeline.py` (or shared types).
- [x] **Enforce Cancellation in Services**
    - [x] Modify `STTService.transcribe` to accept `session_id` and check validity before/after heavy compute.
    - [x] Modify `LLMService.translate` to check validity between tokens (if streaming) or before processing.
    - [x] Modify `TTSService.synthesize` to check validity before synthesis.
- [x] **Integrate with Orchestrator**
    - [x] Update `TranslationPipeline` to initialize `SessionManager`.
    - [x] On PTT Press (Start): Create new session.
    - [x] On PTT Press (Barge-in): Cancel current session.
- [x] **Testing**
    - [x] Unit test `SessionManager` state transitions.
    - [x] Integration test: Simulate long running task, cancel it, verify it aborts.

## Dev Notes

### Architecture & Tech Stack

-   **State Management:** Use `session_id` (UUID4) as the source of truth.
-   **Concurrency Pattern:** "Cooperative Cancellation".
    -   Services must actively check `session_manager.is_valid(payload['session_id'])`.
    -   If invalid, log "Task cancelled" and return early (or raise `CancelledError` if that fits the flow, but simple return is often cleaner for avoiding tracebacks).
-   **Output Clearing:** When cancellation happens, the `AudioPlayer` queue must be drained.

### Project Structure Notes

-   **New File:** `src/app/orchestrator/session.py`
-   **Modified:**
    -   `src/app/orchestrator/pipeline.py` (Inject session manager).
    -   `src/app/services/stt.py`
    -   `src/app/services/llm.py`
    -   `src/app/services/tts.py`

### References

-   **Architecture:** `docs/architecture.md` (State Management: Use `session_id` for cancellation).
-   **Previous Implementation:** `src/app/orchestrator/pipeline.py` (Check how `asyncio.Queue` is currently used).

## Dev Agent Record

### Agent Model Used

antigravity-gemini-3-pro

### Debug Log References

-   Analyzed `sprint-status.yaml`: Story 2.2 is next backlog item.
-   Analyzed `epics.md`: Confirmed requirements for barge-in and cancellation.
-   Analyzed `architecture.md`: Confirmed pattern for Session Management.
-   Analyzed `git log`: Verified async pipeline exists (Commit `92de039`), ensuring this story builds upon it rather than starting from scratch.

### Completion Notes List

- Implemented `SessionManager` in `src/app/orchestrator/session.py` to track and validate sessions.
- Updated `TranslationPipeline` to create sessions on start and cancel them on stop/restart.
- Modified `STTService`, `LLMService`, and `TTSService` to accept `session_manager` and check `session_id` validity before and after heavy operations.
- Updated Payloads in `src/app/core/types.py` to include `session_id`.
- Added unit tests for `SessionManager` and updated service tests.
- Added integration test `tests/integration/test_cancellation.py` confirming pipeline aborts when session is cancelled.

### Review Fixes (2026-01-27)
- Fixed HIGH priority issue: `TranslationPipeline.stop_session` now calls `player.stop()` to ensure immediate audio cut-off and buffer clearing.
- Fixed HIGH priority issue: Added `asyncio.Lock` to `STTService` and `LLMService` to prevent race conditions/crashes during rapid session switching (barge-in).
- Fixed MEDIUM priority issue: Added and committed untracked test files `tests/unit/test_session_manager.py` and `tests/integration/test_cancellation.py`.
- Fixed Test Warnings: Resolved `RuntimeWarning` in tests by properly mocking `tts.synthesize` as an async generator.



### File List

- `src/app/orchestrator/session.py`
- `src/app/core/types.py`
- `src/app/services/stt.py`
- `src/app/services/llm.py`
- `src/app/services/tts.py`
- `src/app/orchestrator/pipeline.py`
- `tests/unit/test_session_manager.py`
- `tests/integration/test_cancellation.py`
- `tests/unit/test_stt.py`
- `tests/unit/test_llm.py`
- `tests/unit/test_tts.py`
- `tests/unit/test_types.py`
- `tests/unit/test_orchestrator_pipeline.py`
