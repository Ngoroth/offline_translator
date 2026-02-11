# Story 2.1: VAD & Auto-Segmentation Logic

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a User,
I want the system to process my speech in segments while I am still holding the button,
so that the translation is ready almost immediately after I finish speaking.

## Acceptance Criteria

1.  **Given** I am holding the PTT key and speaking
2.  **When** I pause for more than `vad_threshold` (e.g., 500ms)
3.  **Then** The system should detect the silence (using existing `webrtcvad` implementation unless quality requires Silero)
4.  **And** "Harvest" the current audio buffer and send it to the STT queue immediately
5.  **And** Continue recording the next segment without user intervention
6.  **And** The system should support tuning the detection thresholds (FR16)
7.  **And** Total latency from VAD detection to STT processing start should be < 200ms (NFR2)

## Tasks / Subtasks

- [x] **Enhance `VADService` (if needed)**
    - [x] Verify `VADService` and `SilenceDetector` in `src/app/utils/vad.py` handle continuous stream analysis.
    - [x] ensure `is_speech` logic is robust for 16kHz float32.
- [x] **Implement Harvest Logic in Orchestrator**
    - [x] Modify `Pipeline` or `InputLoop` to feed audio chunks to `VADService`.
    - [x] Implement state tracking: `Speech -> Silence (Counting) -> Threshold Reached -> Harvest`.
    - [x] On Harvest:
        - [x] Extract buffer from `AudioRecorder` (or internal buffer).
        - [x] Wrap in `STTPayload`.
        - [x] Push to `stt_queue`.
        - [x] Reset buffer/silence counter but *keep recording*.
- [x] **Configuration Updates**
    - [x] Add `vad_threshold` (ms) to `Config` model and `config.yaml`.
    - [x] Add `vad_aggressiveness` to `Config`.
- [x] **Testing**
    - [x] Add unit tests for `SilenceDetector` state transitions.
    - [x] Add integration test with `MockAudioRecorder` injecting pre-recorded speech+silence patterns to verify harvest triggers.

## Dev Notes

### Architecture & Tech Stack

-   **Existing VAD:** `src/app/utils/vad.py` exists and uses `webrtcvad`.
    -   *Constraint:* Epics.md mentions "Silero VAD", but `pyproject.toml` and existing code use `webrtcvad`. **Stick to `webrtcvad`** for now to avoid introducing heavy dependencies (Torch/OnnxRuntime for Silero) on RPi, unless accuracy is unacceptable.
-   **Audio Pipeline:**
    -   `AudioRecorder` puts chunks into an `asyncio.Queue`.
    -   The consumer of this queue (likely in `orchestrator`) must now run VAD checks on every chunk.
-   **Concurrency:**
    -   VAD checks are fast (C++), can likely run in the async loop or `to_thread` if blocking.
    -   Ensure harvesting doesn't block the audio consumer loop (risk of buffer overflow).

### Project Structure Notes

-   **Files to Modify:**
    -   `src/app/utils/vad.py`: Logic refinement.
    -   `src/app/services/stt.py`: Ensure it handles segmented inputs correctly (context continuity?).
    -   `src/app/orchestrator/pipeline.py`: Core logic for VAD loop.
    -   `src/app/core/config.py`: New settings.
    -   `config.yaml`: Default values.

### References

-   **VAD Utils:** `src/app/utils/vad.py`
-   **Audio Recorder:** `src/app/core/audio/recorder.py`
-   **Architecture:** `docs/architecture.md` (Latency requirements)

## Dev Agent Record

### Agent Model Used

gemini-3-pro-preview

### Debug Log References

-   Analysis of `pyproject.toml` confirmed `webrtcvad-wheels` is the established dependency.
-   `src/app/utils/vad.py` contains `SilenceDetector` class which is 80% of the required logic.

### Completion Notes List

-   Updated `sprint-status.yaml` to mark Epic 2 as in-progress.
-   Identified discrepancy between Epic AC (Silero) and implementation (WebRTC); resolved in favor of implementation for consistency.
-   Implemented VAD logic in `TranslationPipeline` using a dedicated `_vad_worker`.
-   Enhanced `VADService` to handle multi-frame chunks robustly by iterating over frames.
-   Added `vad` settings (`threshold_ms`, `aggressiveness`) to `AppSettings` and `config.yaml`.
-   Implemented streaming harvest: when silence is detected, buffer is extracted and sent to STT.
-   Added comprehensive tests: `test_vad_robustness.py` and `test_pipeline_vad.py`.
-   Fixed regression issues in `test_tts.py`, `test_input.py`, and `test_orchestrator_pipeline.py`.
-   **Code Review Fixes (2026-01-27):**
    -   Implemented internal buffering in `VADService` to handle small/variable audio chunks correctly, preventing data loss and false negatives.
    -   Removed broad exception swallowing in `VADService` and fixed logic to prevent crashes while logging errors.
    -   Fixed `tests/unit/test_config_vad.py` to use proper Pydantic models instead of dicts, resolving type safety issues.
    -   Added `tests/unit/test_vad_buffering.py` to verify robustness against small chunks.

### File List

-   `src/app/utils/vad.py`
-   `src/app/orchestrator/pipeline.py`
-   `src/app/core/config.py`
-   `config.yaml`
-   `tests/unit/test_vad_robustness.py`
-   `tests/unit/test_vad_buffering.py`
-   `tests/unit/test_config_vad.py`
-   `tests/integration/test_pipeline_vad.py`
-   `tests/unit/test_tts.py`
-   `tests/unit/test_input.py`
-   `tests/unit/test_orchestrator_pipeline.py`
-   `tests/integration/test_pipeline.py`

