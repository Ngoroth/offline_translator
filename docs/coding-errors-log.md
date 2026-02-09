# Coding Errors Log

This document tracks mistakes made during development to identify patterns and improve processes.

## Session: 2026-02-09 - Raspberry Pi Setup & Input Handler Refactoring

### Error 1: Top-level import of platform-specific library

**File:** `src/app/core/input.py`

**What happened:**
```python
from pynput import keyboard  # Line 6 - unconditional import
```

**Problem:**
`pynput` requires X server on Linux. On headless Raspberry Pi (no GUI), this crashes immediately:
```
ImportError: this platform is not supported: ('failed to acquire X connection: Bad display name ""')
```

**Fix:**
Move import inside the class methods that use it (lazy import):
```python
def start(self) -> None:
    from pynput import keyboard  # Import only when needed
```

**Lesson:**
Platform-specific libraries should use lazy imports inside the classes that need them, not at module level.

---

### Error 2: Lost class declaration during edit

**File:** `src/app/core/input.py`

**What happened:**
When inserting `EvdevInput` class between `KeyboardInput` and `GPIOInput`, the edit accidentally deleted the `class GPIOInput(BaseInput):` line.

Result: GPIOInput methods became orphaned code attached to EvdevInput class.

**LSP errors:**
```
Method declaration "__init__" is obscured by a declaration of the same name
Method declaration "start" is obscured by a declaration of the same name
...
```

**Problem:**
Used an edit that matched only the end of one class, causing the replacement to span incorrectly.

**Fix:**
Include more context in `oldString` to ensure correct match, or read the file first to understand structure.

**Lesson:**
When inserting new classes between existing ones:
1. Read the full file first
2. Include class declaration in the edit context
3. Verify the edit doesn't accidentally span multiple classes

---

### Error 3: Missing configuration model for new feature

**File:** `src/app/core/config.py`, `src/app/main.py`

**What happened:**
Added `EvdevInput` handler with `settings.evdev.device`, but forgot to add `EvdevSettings` model to config.

**LSP error:**
```
Cannot access attribute "evdev" for class "AppSettings"
```

**Fix:**
Add the settings model:
```python
class EvdevSettings(BaseModel):
    device: str = "/dev/input/event0"
```

And add to AppSettings:
```python
evdev: EvdevSettings = EvdevSettings()
```

**Lesson:**
When adding new input handlers or services:
1. Add the implementation class
2. Add the settings model
3. Add settings to AppSettings
4. Update the factory function (get_input_handler)
5. Update config.yaml with example values

---

### Error 4: Config file on Pi not updated with correct input_mode

**File:** `config.yaml` on Raspberry Pi

**What happened:**
Originally set `input_mode: "gpio"` in config, but GPIO is for physical pins, not USB numpad.
USB numpad needs `input_mode: "evdev"`.

**Lesson:**
Different input methods require different handlers:
- `keyboard` - pynput (Windows/Linux with X)
- `evdev` - Linux evdev (USB keyboards/numpads, headless)
- `gpio` - Raspberry Pi GPIO pins (physical buttons)

---

### Error 5: "Blind Run" - Heavy Startup Blocking Input

**File:** `src/app/main.py`

**What happened:**
Tested input handling by running the full application.

**Problem:**
Application takes 60+ seconds to load heavy AI models (LLM, STT). During this time, input handling might not be active, or logs are buffered. User presses buttons with no feedback.

**Solution:**
Create a dedicated `scripts/hardware_check.py` tool.
- Isolate input/hardware logic from AI logic.
- Provide instant feedback (prints/logs).
- Verify hardware integration independently.

**Lesson:**
Never test low-level hardware integration by running the full production stack. Always verify components in isolation first.

### Error 6: Input Event Loop Blocking

**File:** `src/app/core/input.py`

**What happened:**
`EvdevInput` loop might be blocked or not correctly integrated with `asyncio` loop of the main application.

**Problem:**
If `_read_events` task crashes or is not scheduled properly, no input is detected.

**Fix:**
Ensure `EvdevInput` handles its own loop or is correctly awaited. The diagnostic script will verify this.

---

### Error 7: Relying on ALSA/OS for Sample Rate Conversion

**File:** `src/app/core/audio/recorder.py`

**What happened:**
Configured recorder to request 16000Hz from hardware, assuming ALSA `plughw` would handle resampling from the microphone's native 48000Hz.

**Problem:**
PortAudio (via `sounddevice`) often bypasses ALSA plugins or fails to negotiate formats correctly on Raspberry Pi, resulting in `Invalid sample rate` errors.

**Solution:**
Implement software resampling in the application layer.
- Open device at native rate (48k/44.1k).
- Resample (decimate/interpolate) to target rate (16k) in the audio callback.

**Lesson:**
For robust cross-platform audio, do not rely on OS drivers to perform format conversion. Handle it explicitly in the application.

---

### Error 8: "Magic Number" Resampling (Decimation)

**File:** `src/app/core/audio/recorder.py`

**What happened:**
Attempted to downsample 48kHz to 16kHz by taking every 3rd sample (`indata[::3]`).

**Problem:**
While fast, simple decimation without a low-pass filter causes severe **aliasing**. High frequencies fold back into the audible range, creating metallic noise/distortion. Whisper cannot recognize speech in this noise (returns "." or hallucinations).

**Solution:**
Use a proper resampling library (`soxr`, `libsamplerate`) or an external tool (`arecord`, `ffmpeg`) that implements correct DSP filtering.
Alternatively, implement a simple moving average (mean pooling) before decimation, though this is also imperfect.

**Lesson:**
DSP (Digital Signal Processing) requires correct math. "Quick hacks" usually destroy signal quality.

### Error 9: Ignoring "Input Overflow" Warnings

**File:** `src/app/core/audio/recorder.py`

**What happened:**
Logs showed `Audio status: input overflow` repeatedly, but we continued debugging logic errors.

**Problem:**
Overflow means the CPU cannot keep up with the audio stream callback. Data is lost (gaps in audio). VAD and STT fail on corrupted streams.
Cause: Python is too slow for real-time DSP on Raspberry Pi 4, or `blocksize` was too small.

**Solution:**
- Increase `blocksize` (e.g. 4096 -> 8192).
- Move DSP logic out of the Python main thread (use C-level tools via subprocess).

### Error 10: "Big Bang Integration" Anti-Pattern

**Process Error**

**What happened:**
We tried to debug audio input by running the full `main.py` application (which loads LLM, STT, TTS).

**Problem:**
- Slow feedback loop (60s startup time).
- Too many variables (is it the mic? the VAD? the STT? the LLM?).
- Logs were buffered/lost due to crashes.

**Solution:**
**BMAD Principle:** Isolate and Verify.
1. Create `test_recorder.py` FIRST.
2. Verify audio quality (listen to the file).
3. ONLY then integrate into `main.py`.

We eventually did this, but only after wasting an hour on `main.py`.

---

## Patterns to Watch

1. **Platform-specific imports** - Always lazy-load libraries that may not exist on all platforms
2. **Multi-class edits** - Read file structure before editing; include class declarations in context
3. **New features checklist** - Implementation → Settings model → AppSettings → Factory → Config
4. **Config sync** - When changing code, remember to update config on target device
