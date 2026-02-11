# Story 1.4: TTS Service Integration (Piper-TTS)

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Developer,
I want to implement the Text-to-Speech service using Piper-TTS,
So that I can synthesize the translated text into audible speech.

## Acceptance Criteria

1. **Model Loading**: Successfully load an ONNX Piper model from `config.yaml`.
   - Must handle the accompanying `.json` config file automatically.
   - Must support verifying the model loads correctly at startup.
2. **Audio Synthesis**: Implement `TTSService.synthesize(text: str) -> AsyncGenerator[bytes, None]`.
   - Must output raw audio bytes suitable for the audio player.
   - **Crucial**: Output must be **16kHz mono float32** (standard system format).
   - If Piper outputs int16 or different sample rate (e.g. 22kHz), **conversion/resampling is required** before yielding.
3. **Streaming**: The service must support streaming output (yield chunks as they are generated) to minimize latency (NFR1).
4. **Concurrency**: Inference must run in a separate thread (`asyncio.to_thread`) to avoid blocking the main loop.
5. **Offline Only**: No external APIs.
6. **Type Safety**: Strict `basedpyright` compliance (no `Any`).
7. **Interface**: The `synthesize` method should accept a `text` argument and optionally a `voice/lang` identifier (for future dual-language support), defaulting to the configured model.

## Tasks / Subtasks

- [x] **Update Configuration**
  - [x] Update `src/app/core/config.py` with `TTSSettings`.
  - [x] Add `tts_model_path` (validated as file).
  - [x] Add `tts_sample_rate` (optional, to override auto-detection if needed).
- [x] **Implement TTSService** in `src/app/services/tts.py`
  - [x] Create `PiperTTS` class wrapping the `piper` library.
  - [x] Implement `__init__` to load the `.onnx` model and `.json` config.
  - [x] Implement `synthesize` method using `voice.synthesize_stream_raw` (or equivalent).
  - [x] **Implement Audio Conversion**:
    - [x] Convert `int16` bytes from Piper to `float32` numpy array (divide by 32768.0).
    - [x] If model sample rate != 16000, resample to 16000Hz (e.g., using `scipy.signal.resample` or simple decimation if factor is integer, or `librosa` if added). *Note: Use `numpy` or standard libs if possible to avoid heavy dependencies, or check if `sounddevice` or `piper` handles it.*
    - [x] **Constraint**: Do not add heavy audio libs like `librosa` unless absolutely necessary. `scipy` is likely not in `pyproject.toml`. Use `numpy` for simple conversion/resampling if possible, or simple linear interpolation.
  - [x] Wrap blocking calls in `asyncio.to_thread`.
- [x] **Unit Testing**
  - [x] Create `tests/unit/test_tts.py`.
  - [x] Mock `piper.PiperVoice`.
  - [x] Test audio format conversion logic (int16 -> float32).
  - [x] Test error handling (missing model, invalid text).

## Dev Notes

### Critical Implementation Guardrails

- **Audio Format**: The rest of the system (Player, Recorder) expects **16kHz float32**. Piper often defaults to **22050Hz int16**. You **MUST** convert the output.
  - **Int16 to Float32**: `float_data = np.frombuffer(int_data, dtype=np.int16).astype(np.float32) / 32768.0`.
  - **Resampling**: If the model is 22050Hz, simple decimation won't work perfectly for 16kHz. A basic linear interpolation or nearest-neighbor might be too noisy.
  - **Recommendation**: Check if `piper` allows requesting a specific sample rate. If not, implementing a simple `scipy.signal.resample` equivalent or adding `scipy` / `soxr` to dependencies might be needed. **Check `pyproject.toml` first.** `numpy` is available.
- **Streaming**: Do not buffer the entire sentence. Latency is critical. Yield chunks as soon as `piper` gives them.
- **Thread Safety**: Piper's `synthesize` is blocking and CPU heavy.
- **Dependencies**: `piper-tts` is installed. The python module is likely `piper`.

### Project Structure Notes

- **Service**: `src/app/services/tts.py`
- **Config**: `src/app/core/config.py`
- **Tests**: `tests/unit/test_tts.py`

### References

- [Source: epics.md#Story 1.4]
- [Source: architecture.md#Services]

## Dev Agent Record

### Agent Model Used
{{agent_model_name_version}}

### Git Intelligence Summary
- **Previous Story**: `LLMService` used `asyncio.to_thread`. Use the same pattern.
- **Type Checking**: Strict. Use `typing.cast` if `piper` types are missing.

### Latest Technical Information
- `piper-tts` >= 1.3.0 is installed.
- Python module name is `piper`.
- Usage hint:
  ```python
  from piper import PiperVoice
  voice = PiperVoice.load(model_path)
  # synthesize_stream_raw usually yields bytes
  ```

### Completion Notes List
- Implemented `TTSService` using `piper-tts` with async streaming support.
- Added strict type checking with Protocols to handle untyped `piper` library.
- Implemented audio conversion (int16 -> float32) and resampling (linear interpolation) using numpy.
- Added comprehensive unit tests for configuration and synthesis logic.
- Updated `config.py` with `TTSSettings` validation.

### File List
- src/app/services/tts.py
- src/app/core/config.py
- tests/unit/test_tts.py
- tests/unit/test_config_tts.py

## Senior Developer Review (AI)
_Reviewer: Ngoroth on 2026-01-27_

### Findings & Fixes
- **CRITICAL**: The `synthesize` method signature was missing the required `voice/lang` identifier (AC7).
  - **Fix**: Updated `TTSService.synthesize` to accept `speaker_id: int | None`. Updated `PiperVoiceProto` and logic to pass this ID to the underlying Piper voice.
- **MEDIUM**: Performance issue identified where CPU-bound numpy operations (resampling/conversion) were occurring in the main async consumer loop.
  - **Fix**: Refactored `synthesize` to move all numpy processing (int16->float32 conversion and resampling) into the producer thread, ensuring the async loop only handles non-blocking queue consumption.
- **MEDIUM**: `tests/unit/test_config_tts.py` was untracked.
  - **Fix**: Added file to git.

### Outcome
**APPROVED**. All acceptance criteria verified. Code quality improved for latency performance.
