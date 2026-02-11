# Story 2.4: Dual Speaker Role & Language Switching

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a User,
I want to use different keys for different languages (e.g., Space for English, Alt for Russian),
so that I can have a bidirectional conversation without manual configuration changes or looking at a screen.

## Acceptance Criteria

1.  **Given** The config defines Speaker A (e.g., En->Ru) on `input_device_key_a` (e.g., Space) and Speaker B (e.g., Ru->En) on `input_device_key_b` (e.g., Alt/Right Alt).
2.  **When** I press `input_device_key_a` (Speaker A).
3.  **Then** The system initiates a session with Source=English, Target=Russian.
4.  **And** The STT service is hinted to expect English audio.
5.  **And** The LLM service uses the En->Ru system prompt/context.
6.  **And** The TTS service uses the configured Russian voice for output.
7.  **When** I press `input_device_key_b` (Speaker B).
8.  **Then** The system initiates a session with Source=Russian, Target=English.
9.  **And** The STT service is hinted to expect Russian audio.
10. **And** The LLM service uses the Ru->En system prompt/context.
11. **And** The TTS service uses the configured English voice for output.
12. **And** The system supports barge-in correctly regardless of which key is pressed (stopping current playback and starting new session with the *new* key's language direction).

## Tasks / Subtasks

- [x] **Update Configuration Models**
    - [x] Modify `src/app/settings.py` (or `core/config.py`) to include:
        - [x] `speaker_a_key`: str (default "space")
        - [x] `speaker_b_key`: str (default "alt_r" or "shift_r" - ensure distinct from A)
        - [x] `speaker_a_lang`: str (default "en")
        - [x] `speaker_b_lang`: str (default "ru")
        - [x] `speaker_a_voice`: str (default "en_US-libritts-high")
        - [x] `speaker_b_voice`: str (default "ru_RU-ruslan-medium")
- [x] **Enhance Input Service (HAL)**
    - [x] Modify `src/app/core/input.py` (`InputService` and `BaseInput`):
        - [x] Update `wait_for_press()` and `wait_for_release()` (or event callback) to return/emit *which* key was interacted with.
        - [x] Ensure `KeyboardInput` (pynput) correctly maps physical keys to configured `speaker_a_key`/`speaker_b_key`.
- [x] **Update Session Management**
    - [x] Modify `src/app/orchestrator/session.py` (`Session` class):
        - [x] Add `source_lang`, `target_lang`, `tts_voice` fields to `Session` state.
        - [x] Update `SessionManager.start_session()` to accept these parameters.
- [x] **Update Orchestrator Logic**
    - [x] Modify `src/app/orchestrator/orchestrator.py` (or `pipeline.py`):
        - [x] In the main loop (`wait_for_press`), determine which role triggered the event.
        - [x] Retrieve corresponding language pair/voice from Config.
        - [x] Pass these parameters when creating the new Session.
- [x] **Propagate Context to Services**
    - [x] **STT**: Ensure `STTService.transcribe` receives `source_lang` (passed from Session) to optimize whisper decoding.
    - [x] **LLM**: Update `LLMService.translate` to use the correct `source_lang` -> `target_lang` prompt template.
    - [x] **TTS**: Update `TTSService.synthesize` to use the session-specific `tts_voice`.
- [x] **Testing**
    - [x] **Unit Test Config**: Verify default keys and override capability.
    - [x] **Unit Test Input**: Verify correct key identification (A vs B).
    - [x] **Integration Test**:
        - [x] Simulate Key A press -> Verify STT called with Lang A, LLM with A->B, TTS with Voice B.
        - [x] Simulate Key B press -> Verify STT called with Lang B, LLM with B->A, TTS with Voice A.

## Dev Notes

### Architecture & Tech Stack

-   **Input Handling**: `pynput` key names need to be handled carefully (e.g., `Key.space`, `Key.alt_r`). The Config should probably store string representations that `KeyboardInput` maps to `pynput` constants.
-   **State Flow**:
    1.  `InputService` detects `KEY_DOWN(Space)`.
    2.  `Orchestrator` identifies `Space` maps to `Speaker A`.
    3.  `Orchestrator` looks up `Speaker A` config: Source=En, Target=Ru, Voice=Ru_Voice.
    4.  `Orchestrator` starts `Session(id=..., source='en', target='ru', voice='ru_voice')`.
    5.  `Pipeline` passes these session attributes to `STT`, `LLM`, `TTS` payloads.

### Project Structure Notes

-   **Files to Touch**:
    -   `src/app/settings.py` (Config)
    -   `src/app/core/input.py` (Input identification)
    -   `src/app/orchestrator/session.py` (Session context)
    -   `src/app/orchestrator/orchestrator.py` (Logic binding)
    -   `src/app/services/stt.py` (Lang hint)
    -   `src/app/services/llm.py` (Prompt direction)
    -   `src/app/services/tts.py` (Voice selection)

### References

-   **PRD**: FR7 (Language pair selection), FR9 (Speaker role keys).
-   **Architecture**: "IPC: Use ... TypedDict payloads (`STTPayload`, `LLMPayload`)". These payloads must now include language context.
-   **Previous Story (2.3)**: Barge-in logic must now respect the *new* key press. If I'm playing an English translation and hit the "Russian Speaker" key (Alt), I expect to interrupt and start speaking Russian.

## Dev Agent Record

### Agent Model Used

gemini-3-pro-preview

### Debug Log References

### Completion Notes List

- Task 1: Updated `src/app/core/config.py` to include dual speaker settings. Verified with new test `tests/unit/test_config_dual_speaker.py`.
- Task 2: Verified `src/app/core/input.py` handles key mapping correctly via `tests/unit/test_input_mapping.py`. Updated `src/app/main.py` to inject new config keys.
- Task 3: Updated `src/app/orchestrator/session.py` to support rich session context. Verified with `tests/unit/test_session_context.py`.
- Task 4: Updated `src/app/orchestrator/pipeline.py` to initialize session with role-specific config. Verified with `tests/unit/test_pipeline_session_start.py`.
- Task 5: Updated `src/app/services/stt.py` to accept language hint. Updated `src/app/main.py` to load dual speaker voices. Verified STT propagation with `tests/unit/test_stt_language_propagation.py`.
- Task 6: Implemented full pipeline integration test `tests/integration/test_dual_speaker_flow.py` verifying end-to-end dual speaker logic.

### File List

- src/app/core/config.py
- tests/unit/test_config_dual_speaker.py
- src/app/main.py
- tests/unit/test_input_mapping.py
- src/app/orchestrator/session.py
- tests/unit/test_session_context.py
- src/app/orchestrator/pipeline.py
- tests/unit/test_pipeline_session_start.py
- src/app/services/stt.py
- tests/unit/test_stt_language_propagation.py
- tests/integration/test_dual_speaker_flow.py
- tests/unit/test_session_manager.py
- tests/unit/test_orchestrator_pipeline.py
- tests/integration/test_barge_in.py
- src/app/orchestrator/orchestrator.py

## Senior Developer Review (AI)

**Reviewed by:** antigravity-claude-opus-4-5-thinking
**Date:** 2026-01-28

### Review Summary

**Outcome:** APPROVED with fixes applied

**AC Validation:** 12/12 IMPLEMENTED
**Tasks Audit:** All tasks verified complete

### Issues Found & Fixed

| Severity | Issue | Resolution |
|----------|-------|------------|
| HIGH | Language code format inconsistency (session.py defaults "English"/"Russian" vs config "en"/"ru") | Fixed: Changed defaults to ISO codes ("en"/"ru") |
| HIGH | TTS voice path validation missing (defaults were invalid paths like "en_US-libritts-high") | Fixed: Changed defaults to empty string, added validation comments |
| HIGH | Deprecated tts_model_path field still in use | Fixed: Removed deprecated field, updated pipeline.py to use tts_voice |
| MEDIUM | Duplicate input configuration (InputSettings.ptt_a/b vs AppSettings.speaker_a/b_key) | Fixed: Added deprecation comment to InputSettings |
| MEDIUM | Hardcoded language defaults in pipeline.py | Fixed: Use config values as defaults |

### Tests

- **Total:** 78 tests
- **Passed:** 78 (100%)
- **Ruff:** All checks passed
- **Basedpyright:** 0 errors, 1 warning (cosmetic)

### Change Log

- 2026-01-28: Code review completed, 5 issues fixed, status updated to "done"

