# Story 2.3: Barge-In Interruption Support

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a User,
I want to interrupt the current audio playback by pressing the talk button,
so that I can correct a mistake or reply immediately without waiting for the robot to finish.

## Acceptance Criteria

1.  **Given** The system is currently playing audio (TTS output)
2.  **When** I press any PTT key (Space or Alt)
3.  **Then** The audio playback should stop within <50ms (NFR8/NFR7)
4.  **And** The previous session's remaining queue items (STT/LLM/TTS) should be cancelled
5.  **And** A new recording session should start immediately
6.  **And** The `SessionManager` should invalidate the old session
7.  **And** The system should log "Barge-in detected: Cancelling session {id}"

## Tasks / Subtasks

- [x] **Update Audio Player**
    - [x] Modify `src/app/core/audio/player.py`: Implement `stop()` method that:
        - [x] Immediately stops the output stream.
        - [x] Clears the internal audio buffer/queue.
        - [x] Resets internal state to IDLE.
    - [x] Ensure `stop()` is thread-safe and non-blocking.
- [x] **Update Translation Pipeline (State Machine)**
    - [x] Modify `src/app/orchestrator/pipeline.py`:
        - [x] In `_loop` or event handler, detect `InputEvent` (PTT Press) regardless of current state.
        - [x] If state is `PLAYING` or `PROCESSING`:
            - [x] Log barge-in event.
            - [x] Call `self._handle_barge_in()`.
    - [x] Implement `_handle_barge_in()` helper:
        - [x] `self.session_manager.cancel_session(self.current_session_id)`
        - [x] `await self.audio_player.stop()`
        - [x] Drain all `asyncio.Queue`s (stt_queue, llm_queue, tts_queue) to remove stale payloads.
        - [x] Transition state to `RECORDING` immediately.
        - [x] Start new session: `self.current_session_id = self.session_manager.start_session()`.
- [x] **Verify Input Service**
    - [x] Ensure `InputService` events are not blocked by audio playback (verify async event loop isn't blocked by player).
- [x] **Testing**
    - [x] **Unit Test `AudioPlayer`**: Verify `stop()` clears buffer and stops stream.
    - [x] **Integration Test**: Create `tests/integration/test_barge_in.py`:
        - [x] Start a mock playback session.
        - [x] Trigger mock input event.
        - [x] Assert player stopped.
        - [x] Assert old session invalid.
        - [x] Assert new session started.
    - [x] **Latency Check**: Verify stop operation completes in <50ms.

## Dev Notes

### Architecture & Tech Stack

-   **Pattern**: "Barge-in" is a high-priority interrupt.
-   **Concurrency**:
    -   Input events must be processed immediately.
    -   The `AudioPlayer` likely runs in a separate thread (via `sounddevice`) or async task. Ensure `stop()` correctly communicates with it.
-   **State Machine Transitions**:
    -   Current: `IDLE` -> `RECORDING` -> `PROCESSING` -> `PLAYING` -> `IDLE`
    -   New: `PLAYING` -> `RECORDING` (via Barge-in)
    -   New: `PROCESSING` -> `RECORDING` (via Barge-in)

### Project Structure Notes

-   **Modified Files**:
    -   `src/app/orchestrator/pipeline.py` (Core logic)
    -   `src/app/core/audio/player.py` (Stop logic)
    -   `src/app/core/types.py` (If new event types needed, likely existing ones suffice)
-   **New Tests**:
    -   `tests/integration/test_barge_in.py`

### References

-   **PRD**: FR8 (Barge-in interruption), FR12 (Session IDs), UX: "Barge-in Logic".
-   **Architecture**: "Barge-in Mechanism: Global Cancellation Event + Queue Flushing."
-   **Previous Story (2.2)**: `SessionManager` is implemented. Use `session_manager.cancel_session()`.
-   **Git Intelligence**: `tests/integration/test_cancellation.py` exists; `test_barge_in.py` should extend this concept to include PTT triggering.

## Dev Agent Record

### Agent Model Used

antigravity-gemini-3-pro

### Debug Log References

-   **Analyzed Sprint Status**: Confirmed Story 2.3 is next.
-   **Analyzed Epics/PRD**: Validated barge-in requirements (stop audio, clear queues, new session).
-   **Analyzed Architecture**: Confirmed Global Cancellation + Queue Flushing pattern.
-   **Analyzed Previous Story**: Confirmed `SessionManager` availability and usage.
-   **Updated Orchestrator**: Modified `Orchestrator.run` to handle concurrent Barge-in (Input during Processing) by waiting for First Completed task.
-   **Added Tests**: Unit tests for AudioPlayer, Orchestrator (barge-in logic), and Integration test for full flow.

### Completion Notes List

-   **Code Review Fixes (2026-01-27)**:
    -   Fixed race condition in `AudioPlayer.stop()` to ensure thread safety during state transitions.
    -   Updated `tests/integration/test_barge_in.py` to correctly measure latency (<50ms) and verify session invalidation (AC6).
    -   Updated File List to include all touched files including test adjustments.
-   Implemented `AudioPlayer.stop()` with state tracking (IDLE/PLAYING) and `sd.stop()`.
-   Implemented `TranslationPipeline.handle_barge_in()` to handle session cancellation, queue draining, and clean stop.
-   Updated `Orchestrator.run()` to listen for `wait_for_press` concurrently with `wait_for_completion` when session is active.
-   Verified `InputService` is non-blocking (pynput in thread).
    -   Added `tests/integration/test_barge_in.py` verifying full barge-in flow (Stop Playback -> New Session) and latency (<0.4s end-to-end including overhead).
-   **Quality Gates**:
    -   Ran `basedpyright` and fixed 2 errors in `orchestrator.py` and missing type annotations in new tests.
    -   Ensured zero type errors in production code.

### File List

- src/app/core/audio/player.py
- src/app/orchestrator/pipeline.py
- src/app/orchestrator/orchestrator.py
- tests/unit/test_player_barge_in.py
- tests/unit/test_orchestrator_barge_in.py
- tests/integration/test_barge_in.py
- tests/unit/test_orchestrator.py
- tests/integration/test_cancellation.py
- tests/unit/test_config_vad.py
- tests/unit/test_session_manager.py
- tests/unit/test_tts.py
- tests/unit/test_vad_buffering.py
