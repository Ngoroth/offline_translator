---
phase: 03-startup-verification
plan: 01
subsystem: core
tags: [startup, validation, models, audio-devices, exit-codes]

# Dependency graph
requires:
  - phase: 02-audio-device-discovery
    provides: Audio device enumeration (list_audio_devices, get_default_*_device)
provides:
  - StartupVerifier class for startup prerequisite validation
  - Exit code 1 for missing models, 2 for missing audio
  - Plain text error messages with actionable guidance
affects: [main.py, config.py, startup verification]

# Tech tracking
tech-stack:
  added: []
  patterns: [early exit pattern, plain text error output]

key-files:
  created: [src/app/core/startup.py]
  modified: [src/app/main.py, src/app/core/config.py, tests/unit/test_config_tts.py, tests/unit/test_config_validation.py, tests/smoke/test_real_config_loading.py]

key-decisions:
  - "Moved file existence validation from pydantic to StartupVerifier for clean exit behavior"
  - "Exit code 1 for missing models, 2 for missing audio devices"
  - "Plain text output (no colors, no JSON) for headless RPi compatibility"

patterns-established:
  - "Startup verification runs before hardware initialization"
  - "Model validation checks local paths only (huggingface IDs skipped)"

requirements-completed: [VERF-01, VERF-02, VERF-03, VERF-04]

# Metrics
duration: 9min
completed: 2026-02-19
---

# Phase 3 Plan 1: Startup Verification Summary

**StartupVerifier class validates models and audio devices at startup with clean exit codes and plain text error messages**

## Performance

- **Duration:** 9 min
- **Started:** 2026-02-19T05:20:07Z
- **Completed:** 2026-02-19T05:28:43Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Created StartupVerifier class with verify_models() and verify_audio_devices() methods
- Integrated startup verification into main.py before hardware initialization
- Removed pydantic file existence validators (validation now in StartupVerifier)
- Updated tests to reflect deferred file validation pattern

## Task Commits

Each task was committed atomically:

1. **Task 1: Create StartupVerifier class in core/startup.py** - `8f79b6d` (feat)
2. **Task 2: Integrate StartupVerifier into main.py startup sequence** - `42ce743` (feat)
3. **Test fixes for deferred file validation** - `ce3b32a` (fix)

**Plan metadata:** (to be committed with docs)

## Files Created/Modified

- `src/app/core/startup.py` - StartupVerifier class with model and audio device validation
- `src/app/main.py` - Added startup verification call after config load
- `src/app/core/config.py` - Removed file existence validators (TTSSettings and AppSettings)
- `tests/unit/test_config_tts.py` - Updated to test non-existent path acceptance
- `tests/unit/test_config_validation.py` - Updated to test missing file acceptance
- `tests/smoke/test_real_config_loading.py` - Added 'evdev' to valid input modes

## Decisions Made

- **Moved file existence validation from pydantic to StartupVerifier**: Pydantic validators raised structured ValidationError without clean exit codes. StartupVerifier provides plain text messages with exit codes 1/2 as specified by user.
- **Kept model validation pattern from RESEARCH.md**: STT model path only validated if it looks like a local path (absolute or starts with "models/"), allowing huggingface IDs to work.
- **Plain text output**: No colors, no JSON, no rich formatting - compatible with headless RPi deployment.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Removed pydantic file existence validators**
- **Found during:** Task 2 (integration verification)
- **Issue:** Pydantic validators in config.py were catching missing models before StartupVerifier could run, preventing clean exit with code 1 and plain text message. The pydantic ValidationError output is structured, not plain text.
- **Fix:** Removed TTSSettings.validate_model_path field_validator and AppSettings.validate_file_existence model_validator. File existence validation now exclusively handled by StartupVerifier.
- **Files modified:** src/app/core/config.py
- **Verification:** Running `uv run python src/app/main.py` with missing models now exits with code 1 and prints plain text error message.
- **Committed in:** 42ce743 (Task 2 commit)

**2. [Rule 3 - Blocking] Updated tests to match new validation behavior**
- **Found during:** Post-task verification (pytest run)
- **Issue:** Tests expected ValidationError for missing/non-existent model files, but this validation was moved to StartupVerifier.
- **Fix:** Updated tests to verify that config loading accepts non-existent paths (validation deferred to startup):
  - test_tts_settings_validation_file_not_found → test_tts_settings_accepts_nonexistent_path
  - test_config_validation_missing_llm now tests that missing files are accepted
  - test_load_real_config updated to include 'evdev' in valid input modes
- **Files modified:** tests/unit/test_config_tts.py, tests/unit/test_config_validation.py, tests/smoke/test_real_config_loading.py
- **Verification:** All 142 tests pass
- **Committed in:** ce3b32a (separate fix commit)

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both fixes necessary to achieve user requirements (exit codes, plain text output). No scope creep.

## Issues Encountered

None - all issues resolved via deviation rules.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Startup verification complete and tested
- Ready for Plan 02 (error handling improvements)
- Tests passing, type checking and linting clean

---
*Phase: 03-startup-verification*
*Completed: 2026-02-19*

## Self-Check: PASSED

- [x] src/app/core/startup.py exists
- [x] SUMMARY.md exists
- [x] All commits found: 8f79b6d, 42ce743, ce3b32a, 6b076b9
