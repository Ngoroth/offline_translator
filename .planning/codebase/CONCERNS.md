# Codebase Concerns

**Analysis Date:** 2026-02-17

## Tech Debt

### GPIO Active Low Hardcoding
- **Issue:** GPIO input active-low logic is hardcoded in `src/app/core/input.py` line 377
- **Files:** `src/app/core/input.py` (line 377)
- **Impact:** Cannot use active-high GPIO configurations without code modification
- **Fix approach:** Make `active_low` configurable via `GPIOSettings` (field exists but is unused)
- **Priority:** Low - GPIO not used on target device (uses USB numpad via evdev)

### Legacy Input Settings
- **Issue:** `InputSettings.ptt_a` and `ptt_b` are marked for removal but still exist
- **Files:** `src/app/core/config.py` (lines 81-83)
- **Impact:** Confusion between old and new dual-speaker configuration
- **Fix approach:** Migrate all configs and remove legacy fields

### TTS Sample Rate Assumption
- **Issue:** Per-voice sample rate handling is not implemented - assumes all voices use same rate
- **Files:** `src/app/services/tts.py` (line 86)
- **Impact:** Mixing voices with different sample rates will cause audio distortion
- **Fix approach:** Calculate resampling per voice in `synthesize()` method

### Error Handler Swallows Exceptions
- **Issue:** VAD error handler silently passes on exceptions
- **Files:** `src/app/utils/vad.py` (lines 44-49)
- **Impact:** VAD failures are invisible, leading to mysterious behavior
- **Fix approach:** Add proper logging or re-raise with context

## Known Bugs

### EvdevInput Loop Context Bug
- **Symptoms:** "EvdevInput.start() must be called from within an async context" error if loop not running
- **Files:** `src/app/core/input.py` (lines 183-189)
- **Trigger:** Calling `start()` outside async context
- **Workaround:** Always call from async context

### Recorder Thread Safety
- **Symptoms:** `_loop` may be uninitialized if recorder created outside async context
- **Files:** `src/app/core/audio/recorder.py` (lines 31-35)
- **Trigger:** Creating recorder before event loop exists
- **Workaround:** Ensure async context exists before instantiation

### OutputProvider is Unimplemented
- **Symptoms:** Abstract base class exists but no concrete implementations
- **Files:** `src/app/core/output.py`
- **Trigger:** N/A - not currently used
- **Workaround:** Use logging directly

## Security Considerations

### No Input Sanitization on Model Paths
- **Risk:** Path traversal possible if config.yaml is compromised
- **Files:** `src/app/core/config.py` model validators
- **Current mitigation:** Basic file existence checks
- **Recommendations:** Validate paths don't escape model directory, use allowlist

### Subprocess Injection via Device Index
- **Risk:** Malicious device string could inject commands into arecord
- **Files:** `src/app/core/audio/recorder.py` (lines 55, 63-78)
- **Current mitigation:** None
- **Recommendations:** Validate device string against allowed ALSA device pattern

### YAML Loading Without Schema Validation
- **Risk:** YAML could contain arbitrary Python objects
- **Files:** `src/app/core/config.py` (line 183)
- **Current mitigation:** Uses `safe_load`
- **Recommendations:** Consider adding schema validation

## Performance Bottlenecks

### STT Lock Contention
- **Problem:** Single asyncio lock for model access blocks concurrent STT operations
- **Files:** `src/app/services/stt.py` (line 118)
- **Cause:** Lock held during entire transcription
- **Improvement path:** Consider connection pooling or model sharding for multi-session

### LLM Synchronous Initialization
- **Problem:** LLM model loads synchronously in `__init__`, blocking event loop
- **Files:** `src/app/services/llm.py` (lines 48-63)
- **Cause:** `Llama()` constructor is CPU-intensive and blocking
- **Improvement path:** Lazy loading or move to thread like STT

### Audio Player Blocking
- **Problem:** `sd.play(blocking=True)` blocks the thread
- **Files:** `src/app/core/audio/player.py` (line 34)
- **Cause:** Uses blocking playback
- **Improvement path:** Already wrapped in `asyncio.to_thread()` in pipeline

### Memory Pressure from Ring Buffer
- **Problem:** 10-second audio ring buffer may be excessive for long PTT holds
- **Files:** `src/app/core/audio.py` (line 20)
- **Cause:** Fixed-size buffer
- **Improvement path:** Make configurable based on expected speech duration

## Fragile Areas

### Multi-Input Handler State Management
- **Files:** `src/app/core/input.py`
- **Why fragile:** Three different input implementations (Keyboard, Evdev, GPIO) with slightly different async patterns
- **Note:** EvdevInput is the production input method on target device; GPIO is available but not used
- **Safe modification:** Ensure all handlers implement `BaseInput` contract exactly
- **Test coverage:** Unit tests exist but don't cover all edge cases

### Pipeline Worker Cancellation
- **Files:** `src/app/orchestrator/pipeline.py`
- **Why fragile:** Multiple worker tasks with complex cancellation flow, race conditions possible
- **Safe modification:** Always use `asyncio.gather(*tasks, return_exceptions=True)` and handle CancelledError
- **Test coverage:** Cancellation tests exist in `tests/integration/test_cancellation.py`

### Session ID Propagation
- **Files:** All service files (`stt.py`, `llm.py`, `tts.py`)
- **Why fragile:** Cancellation check pattern repeated across all services, easy to miss a check
- **Safe modification:** Create decorator or middleware for session validation
- **Test coverage:** Unit tests for cancellation exist

### TTS Resampling Logic
- **Files:** `src/app/services/tts.py` (lines 156-230)
- **Why fragile:** Complex numpy interpolation with index tracking, easy to introduce off-by-one errors
- **Safe modification:** Add extensive unit tests for edge cases
- **Test coverage:** Basic tests exist, edge case coverage unclear

## Scaling Limits

### Single LLM Instance
- **Current capacity:** 1 concurrent translation
- **Limit:** Cannot handle overlapping speech from both speakers
- **Scaling path:** Would need session isolation or model replication

### Queue Size Unbounded
- **Current capacity:** Unlimited (asyncio.Queue default)
- **Limit:** Memory exhaustion under high load
- **Scaling path:** Add maxsize to queues and backpressure handling

### Thread Pool Size
- **Current capacity:** Default asyncio thread pool
- **Limit:** Blocking operations (STT, LLM, TTS) all share same pool
- **Scaling path:** Dedicated thread pools per service type

## Dependencies at Risk

### `llama-cpp-python`
- **Risk:** Complex native dependency with frequent breaking changes
- **Impact:** Model loading or inference could break on updates
- **Migration plan:** Pin to specific version, monitor changelogs

### `piper-tts`
- **Risk:** Smaller project, less maintenance
- **Impact:** TTS failures if abandoned
- **Migration plan:** Alternative TTS backends (coqui, melotts)

### `lgpio` (Raspberry Pi GPIO)
- **Risk:** Linux-only, specific to RPi hardware
- **Impact:** Cannot run GPIO mode on other platforms
- **Mitigation:** GPIO not used on target device (uses USB numpad via evdev)
- **Migration plan:** Maintain abstraction layer, already done via `BaseInput`

## Missing Critical Features

### Audio Device Auto-Discovery
- **Problem:** USB device indices change after reboot
- **Blocks:** Reliable deployment on Raspberry Pi
- **Priority:** High (in BACKLOG.md Story 1.2)

### Echo/Passthrough Mode
- **Problem:** Cannot test audio I/O without loading all AI models
- **Blocks:** Quick hardware validation
- **Priority:** High (in BACKLOG.md Story 2.1)

### Auditory Feedback
- **Problem:** No audio cues for system state (startup, listening, error)
- **Blocks:** User-friendly operation
- **Priority:** Medium (in BACKLOG.md Story 2.2)

### Hardware Validation Script
- **Problem:** No unified diagnostic tool
- **Blocks:** Troubleshooting deployment issues
- **Priority:** Medium (in BACKLOG.md Story 3.1)

## Test Coverage Gaps

### Error Path Testing
- **What's not tested:** Many exception handlers in pipeline workers
- **Files:** `src/app/orchestrator/pipeline.py` exception blocks (lines 235, 344, 387, 417, 442)
- **Risk:** Error handling bugs go unnoticed
- **Priority:** Medium

### GPIO Input Hardware Testing
- **What's not tested:** Actual GPIO hardware interactions
- **Files:** `src/app/core/input.py` `GPIOInput` class
- **Risk:** GPIO bugs only caught on actual hardware
- **Priority:** Low (mock-based unit tests exist; GPIO not used on target device which uses USB numpad via evdev)

### Audio Hardware Edge Cases
- **What's not tested:** Buffer underruns, device disconnects
- **Files:** `src/app/core/audio/recorder.py`, `src/app/core/audio/player.py`
- **Risk:** Audio hardware failures not handled gracefully
- **Priority:** Medium

### TTS Resampling Edge Cases
- **What's not tested:** Empty chunks, extreme resampling ratios
- **Files:** `src/app/services/tts.py` resampling logic
- **Risk:** Audio artifacts or crashes
- **Priority:** Low

## Code Quality Issues

### Inconsistent Exception Handling
- **Problem:** Mix of broad `except Exception:` and specific exceptions
- **Files:** Throughout codebase
- **Recommendation:** Standardize on domain-specific exceptions

### Missing Type Stubs
- **Problem:** Several dependencies lack type stubs
- **Files:** `pyproject.toml` reports disabled for unknown types
- **Recommendation:** Create typings in `src/typings/` directory

### Print Statement in Production Code
- **Problem:** `print()` used in audio callback instead of logger
- **Files:** `src/app/core/audio.py` (line 30)
- **Recommendation:** Replace with proper logging

---

*Concerns audit: 2026-02-17*
