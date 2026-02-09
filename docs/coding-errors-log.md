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

## Patterns to Watch

1. **Platform-specific imports** - Always lazy-load libraries that may not exist on all platforms
2. **Multi-class edits** - Read file structure before editing; include class declarations in context
3. **New features checklist** - Implementation → Settings model → AppSettings → Factory → Config
4. **Config sync** - When changing code, remember to update config on target device
