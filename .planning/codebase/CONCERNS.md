# Codebase Concerns

**Analysis Date:** 2026-02-20

## Tech Debt

**Legacy PTT Configuration:**
- Issue: `InputSettings` class contains legacy `ptt_a`/`ptt_b` fields marked for removal
- Files: `src/app/core/config.py:74-76`
- Impact: Config duplication with `speaker_a_key`/`speaker_b_key`, potential confusion
- Fix approach: Remove `InputSettings` class and migrate all configs to speaker keys

**Hardcoded GPIO Active State:**
- Issue: GPIO `active_low` is hardcoded to `True` (press = 0) but setting exists in `GPIOSettings`
- Files: `src/app/core/input.py:377`, `src/app/core/config.py:62`
- Impact: Breaks with active-high button hardware
- Fix approach: Wire `GPIOSettings.active_low` to `GPIOInput` constructor and use in `_gpio_callback`

**Per-Voice Sample Rate Handling:**
- Issue: TTS assumes all voices have same sample rate; resampling calculated once
- Files: `src/app/services/tts.py:86`
- Impact: Audio corruption if multi-voice setup uses different-rate models
- Fix approach: Calculate resampling per-synthesis call based on selected voice

**Duplicate AudioRecorder Implementations:**
- Issue: Two `AudioRecorder` classes exist - one using `sounddevice` (audio.py), one using `arecord` subprocess (recorder.py)
- Files: `src/app/core/audio.py:7-72`, `src/app/core/audio/recorder.py:24-186`
- Impact: Confusion about which is used; `main.py` imports from `audio.recorder`
- Fix approach: Remove unused sounddevice-based `AudioRecorder` from `audio.py`

## Known Bugs

**No Critical Bugs Identified:**
- Codebase appears stable for current use cases
- All identified issues are tech debt or edge cases rather than bugs

## Security Considerations

**Subprocess Command Construction:**
- Risk: `arecord` command built with device name from config; shell injection possible if config compromised
- Files: `src/app/core/audio/recorder.py:67-80`
- Current mitigation: Uses `subprocess.Popen` with list args (not shell=True), no shell interpolation
- Recommendations: Validate device name format (alphanumeric + `:,._-` only)

**Config File Loading:**
- Risk: YAML loading without schema restrictions
- Files: `src/app/core/config.py:143-145`
- Current mitigation: `yaml.safe_load` used (prevents arbitrary object instantiation)
- Recommendations: Consider adding file permission checks (config shouldn't be world-writable)

**No Authentication/Audit:**
- Risk: No logs of who used the system (relevant for multi-user deployments)
- Files: Entire codebase
- Current mitigation: Not applicable (single-user device)
- Recommendations: Add optional audit logging if deployed in shared environments

## Performance Bottlenecks

**Synchronous LLM Model Loading:**
- Problem: `_init_model()` called in `__init__`, blocks startup for several seconds
- Files: `src/app/services/llm.py:46,48-63`
- Cause: `llama-cpp-python` loads model synchronously
- Improvement path: Defer model loading to first use (like STT) or load in background thread

**Single-Threaded LLM Inference:**
- Problem: `asyncio.Lock` prevents concurrent translations even for different sessions
- Files: `src/app/services/llm.py:90`
- Cause: `llama-cpp-python` model not thread-safe
- Improvement path: Accept sequential processing for now; consider model sharding for scale

**TTS Resampling Algorithm:**
- Problem: Linear interpolation in Python loop, not vectorized
- Files: `src/app/services/tts.py:193-230`
- Cause: Custom resampling implementation
- Improvement path: Use `scipy.signal.resample` or `librosa` for better quality/performance

**VAD Buffer Accumulation:**
- Problem: `VADService._buffer` grows if frames come in smaller than 30ms chunk
- Files: `src/app/utils/vad.py:21,31`
- Cause: Buffer never truncated if frames are too small
- Improvement path: Add max buffer size with warning log

## Fragile Areas

**VAD Worker / Buffer Extraction Race:**
- Files: `src/app/orchestrator/pipeline.py:199-206,277`
- Why fragile: VAD worker calls `recorder.extract_buffer()` while main loop may also access
- Safe modification: Ensure VAD task is cancelled before `handle_input_complete()` extracts buffer (already done)
- Test coverage: Covered in `test_pipeline_vad.py`

**Audio Device Enumeration Failures:**
- Files: `src/app/core/audio/devices.py:32-44`
- Why fragile: `sd.query_devices()` can throw; error only logged, empty list returned
- Safe modification: Wrap calls in try/except, return sentinel value for "enumeration failed"
- Test coverage: Partial - `test_list_audio_devices_empty` covers some cases

**Cross-Platform Audio Backend:**
- Files: `src/app/core/audio/recorder.py:67-80` (arecord), `src/app/core/audio/player.py:33` (sounddevice)
- Why fragile: Recorder uses `arecord` (Linux-only), Player uses `sounddevice` (cross-platform)
- Safe modification: Add platform detection and fallback; document Linux requirement
- Test coverage: Not tested on Windows (arecord not available)

**Barge-In Cancellation Timing:**
- Files: `src/app/orchestrator/orchestrator.py:30-54`
- Why fragile: Complex `asyncio.wait` with `FIRST_COMPLETED` for press vs completion race
- Safe modification: Add explicit state checks before transitions
- Test coverage: `test_orchestrator_barge_in.py` covers happy path

**KeyboardInput Event Loop Access:**
- Files: `src/app/core/input.py:68-71`
- Why fragile: `asyncio.get_running_loop()` called in `__init__`, may fail if not in async context
- Safe modification: Defer loop capture to `start()` method
- Test coverage: Warning logged but not tested

## Scaling Limits

**Single Active Session:**
- Current capacity: One session at a time
- Limit: `SessionManager` tracks set of session IDs but pipeline only holds one `self.session`
- Scaling path: Refactor to support concurrent sessions with separate worker pools

**Audio Buffer Memory:**
- Current capacity: 10 seconds ring buffer (~640KB at 16kHz float32)
- Limit: `AudioRingBuffer` capacity fixed at construction
- Scaling path: Make capacity configurable; add memory monitoring

**LLM Context Window:**
- Current capacity: 512-4096 tokens depending on profile
- Limit: Long conversations may lose context
- Scaling path: Implement conversation summarization or sliding window

**Model Memory Footprint:**
- Current capacity: ~1.5GB combined (STT + LLM + TTS)
- Limit: Raspberry Pi 4 (2GB) leaves ~500MB for OS
- Scaling path: Use quantized models; implement model swapping

## Dependencies at Risk

**evdev (Linux-only):**
- Risk: Required for headless USB input on RPi; not installable on Windows
- Impact: `EvdevInput` class unusable on development machines
- Migration plan: Keep as optional dependency; document platform requirements

**lgpio (Linux-only):**
- Risk: GPIO library for Raspberry Pi; requires `lgpio` system package
- Impact: `GPIOInput` fails gracefully with ImportError but no alternative
- Migration plan: Keep as optional; consider `RPi.GPIO` or `gpiozero` as alternatives

**pynput (requires X on Linux):**
- Risk: Desktop keyboard input; fails headless without X server
- Impact: Development uses keyboard, deployment uses evdev/GPIO
- Migration plan: Already handled by input_mode config switch

**faster-whisper (CTranslate2 dependency):**
- Risk: Native library; may have platform-specific issues
- Impact: Core STT functionality
- Migration plan: Fallback to `openai-whisper` (slower but pure Python)

## Missing Critical Features

**No Critical Gaps Identified:**
- Feature set matches MVP requirements for offline speech-to-speech translation
- Dual speaker support implemented
- Barge-in handling implemented
- Multiple input modes supported

## Test Coverage Gaps

**EvdevInput Integration:**
- What's not tested: Actual evdev device reading, key mapping, async queue behavior
- Files: `src/app/core/input.py:152-275`
- Risk: Input handling broken on RPi deployment without detection
- Priority: High (deployment-critical)

**AudioRecorder (sounddevice variant):**
- What's not tested: The `AudioRecorder` in `audio.py` (appears unused)
- Files: `src/app/core/audio.py:7-72`
- Risk: Dead code that may be accidentally used
- Priority: Low (if confirmed unused, should be removed)

**Error Path Coverage:**
- What's not tested: Network failures during model download, disk full, permission denied
- Files: `scripts/download_models.py`
- Risk: Silent failures during setup
- Priority: Medium

**Long-Running Session Memory:**
- What's not tested: Memory behavior over hours of continuous operation
- Files: Pipeline and buffer code
- Risk: Memory leak causing OOM on RPi
- Priority: Medium

**Concurrent PTT Presses:**
- What's not tested: Both buttons pressed simultaneously
- Files: `src/app/orchestrator/orchestrator.py`
- Risk: Undefined behavior or race condition
- Priority: Low (edge case)

---

*Concerns audit: 2026-02-20*
