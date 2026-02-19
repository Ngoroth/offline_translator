# Phase 3: Startup Verification - Research

**Researched:** 2026-02-18
**Domain:** Python startup validation, error handling, exit codes
**Confidence:** HIGH

## Summary

Phase 3 implements startup verification that validates models exist and audio devices are available before user interaction begins. The codebase already has partial validation infrastructure in `config.py` (model file existence via pydantic validator) and `main.py` (audio device resolution). The key work is reorganizing this into a dedicated startup verification module with clean exit behavior and plain text error output.

**Primary recommendation:** Create a `StartupVerifier` class in `core/startup.py` that runs checks before the main application starts, halting with actionable error messages and non-zero exit codes when prerequisites are missing.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions

- Only two checks: models exist, audio devices available
- No USB numpad detection (device uses USB numpad, not GPIO)
- No resource threshold checks (RAM/CPU)
- No config validation

### Missing models behavior
- Halt startup immediately
- Print expected model paths to console
- Exit with error code

### Missing audio device behavior
- Halt startup immediately
- Print list of available audio devices
- Exit with error code

### Output format
- Plain text (no colors, no JSON)

### Logging
- Console only, no log files

### Claude's Discretion
- Exact error message wording
- Exit codes (non-zero for errors)
- Order of checks

### Deferred Ideas (OUT OF SCOPE)
- GPIO support removed from scope — USB numpad is the input device
- Resource threshold warnings — not needed for this phase

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| VERF-01 | System validates model files exist at startup | `pathlib.Path.exists()` for file checks; current validation in `config.py:127-155` |
| VERF-02 | System validates model files load successfully | Service constructors already raise exceptions; can attempt import/load |
| VERF-03 | System provides clear error messages for missing models | Print expected paths + exit code 1; see error message patterns below |
| VERF-04 | System checks audio device availability at startup | `list_audio_devices()` in `devices.py`; `get_default_input_device()` / `get_default_output_device()` |
| VERF-05 | System validates configuration at startup | **DEFERRED** - out of scope per CONTEXT.md |
| VERF-06 | System checks minimum resources (RAM, CPU) | **DEFERRED** - out of scope per CONTEXT.md |
| ERRO-01 | VAD errors are logged (not silently swallowed) | Fix `pass` at `vad.py:44-49`; add logger.error() |
| ERRO-02 | Pipeline errors include actionable context | Enhance existing logger.error() calls with context dict |
| ERRO-03 | GPIO active_low configuration is actually used | **DEFERRED** - out of scope per CONTEXT.md |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `sys` | stdlib | Exit codes via `sys.exit()` | Standard Python CLI pattern |
| `pathlib` | stdlib | File existence checks | Cross-platform path handling |
| `pydantic` | 2.0.0+ | Settings validation | Already in use for config |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `loguru` | 0.7.3+ | Structured logging | Already in use; keep for errors |
| `sounddevice` | 0.5.5+ | Audio device enumeration | Already wrapped in `devices.py` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `sys.exit()` | `raise SystemExit` | Same effect; `sys.exit()` more readable |
| Custom verifier | Extend pydantic validators | Pydantic validators raise ValidationError, not clean exit |

## Architecture Patterns

### Recommended Module Structure
```
src/app/
├── core/
│   ├── startup.py         # NEW: StartupVerifier class
│   ├── startup_errors.py  # NEW: Custom exceptions with exit codes
│   ├── config.py          # Existing: keep model validators as backup
│   └── audio/
│       └── devices.py     # Existing: device discovery
└── main.py                # Modified: call verifier before init
```

### Pattern 1: Startup Verifier with Early Exit

**What:** Dedicated verification class that runs before any service initialization.

**When to use:** CLI applications that require prerequisites (files, devices, resources).

**Example:**
```python
# core/startup.py
import sys
from pathlib import Path
from app.core.audio.devices import list_audio_devices, get_default_input_device, get_default_output_device

class StartupVerifier:
    def __init__(self, settings: AppSettings):
        self.settings = settings
        self.exit_code = 0

    def verify_all(self) -> bool:
        """Run all checks. Returns True if all pass, exits otherwise."""
        if not self.verify_models():
            sys.exit(self.exit_code)
        if not self.verify_audio_devices():
            sys.exit(self.exit_code)
        return True

    def verify_models(self) -> bool:
        """Check all model files exist. Print missing paths if not."""
        missing = self._get_missing_models()
        if missing:
            print("ERROR: Missing model files:")
            for path in missing:
                print(f"  - {path}")
            print("\nRun: uv run python scripts/download_models.py")
            self.exit_code = 1
            return False
        return True

    def verify_audio_devices(self) -> bool:
        """Check audio devices available. Print available devices if not."""
        devices = list_audio_devices()
        input_dev = get_default_input_device()
        output_dev = get_default_output_device()

        if not input_dev or not output_dev:
            print("ERROR: No audio devices available")
            print("\nAvailable devices:")
            for dev in devices:
                kind = []
                if dev.is_input:
                    kind.append("input")
                if dev.is_output:
                    kind.append("output")
                print(f"  [{dev.index}] {dev.name} ({', '.join(kind)})")
            self.exit_code = 2
            return False
        return True
```

### Pattern 2: Exit Code Conventions

**What:** Standard exit codes for different failure types.

**Convention:**
| Code | Meaning | When to Use |
|------|---------|-------------|
| 0 | Success | All checks passed |
| 1 | General error / Missing files | Model files not found |
| 2 | Configuration error | Audio devices not available |
| 64-78 | BSD sysexits.h range | Optional: more specific errors |

**Reference:** Python's `os.EX_*` constants (Unix only), standard CLI convention is 1 for any error.

### Pattern 3: Plain Text Error Output

**What:** Print errors to stdout/stderr without colors, formatting, or JSON.

**Why:** User decision requires plain text for compatibility with headless RPi deployment.

**Example output:**
```
ERROR: Missing model files:
  - models/llm/Qwen3-4B-Instruct-2507-Q4_K_M.gguf
  - models/tts/en_US-libritts_r-medium.onnx

Run: uv run python scripts/download_models.py
```

### Anti-Patterns to Avoid
- **Rich/colored output:** User explicitly wants plain text
- **JSON error format:** User explicitly rejected JSON
- **Continuing on error:** Must halt immediately, not try to recover
- **Swallowing exceptions:** Must surface all errors with actionable messages

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| File existence check | Custom path validation | `Path.exists()` | stdlib, handles edge cases |
| Audio device list | Custom sounddevice calls | `list_audio_devices()` | Already exists in codebase |
| Model path collection | Hardcoded paths | Settings object | Config-driven, already exists |

## Common Pitfalls

### Pitfall 1: Checking Models That Don't Need Files
**What goes wrong:** faster-whisper accepts model names like "tiny", "small" that don't require local files (downloaded to cache).

**Why it happens:** STT model_path can be either a local path OR a huggingface model ID.

**How to avoid:** Check if path looks like a local path before validating existence:
```python
p = Path(model_path)
if p.is_absolute() or str(model_path).startswith("models/"):
    if not p.exists():
        # This is an error
```
**Note:** This pattern already exists in `config.py:134-137`.

### Pitfall 2: Audio Device Check Fails on Windows
**What goes wrong:** RPi uses ALSA devices (plughw:X,Y), Windows uses different backend.

**Why it happens:** Development is on Windows, deployment on RPi.

**How to avoid:** The `sounddevice` library already abstracts this. `list_audio_devices()` works on both platforms.

### Pitfall 3: VAD Errors Silently Swallowed
**What goes wrong:** Exception in `vad.is_speech()` is caught with bare `pass`, hiding potential issues.

**Why it happens:** Original code prioritized "don't crash" over "surface errors".

**How to avoid:** Replace `pass` with `logger.error()`:
```python
except Exception as e:
    logger.error(f"VAD error: {e}")
    # Still continue, but now we have visibility
```

### Pitfall 4: Pipeline Error Context Missing
**What goes wrong:** `logger.error(f"STT Error: {e}")` doesn't include session context.

**Why it happens:** Simpler logging initially, context not considered.

**How to avoid:** Include relevant context in error logs:
```python
logger.error(f"STT Error: {e}", extra={
    "session_id": session_id,
    "audio_length": len(payload["audio"]),
})
```

## Code Examples

### Model Verification (Existing Pattern to Adapt)
```python
# From config.py:127-155 - Current pydantic validator
@model_validator(mode="after")
def validate_file_existence(self) -> "AppSettings":
    # STT
    if self.stt.model_path and not Path(self.stt.model_path).exists():
        p = Path(self.stt.model_path)
        if p.is_absolute() or str(self.stt.model_path).startswith("models/"):
            if not p.exists():
                raise ValueError(f"STT Model not found: {self.stt.model_path}")

    # LLM
    if self.llm.model_path and not Path(self.llm.model_path).exists():
        raise ValueError(f"LLM Model not found: {self.llm.model_path}")

    # TTS (Default)
    if self.tts.model_path and not Path(self.tts.model_path).exists():
        raise ValueError(f"TTS Model not found: {self.tts.model_path}")

    # ... speaker voices ...

    return self
```

### Audio Device Check (Existing Implementation)
```python
# From main.py:69-104 - Current device validation
devices = list_audio_devices()
logger.info(f"Found {len(devices)} audio devices")

input_device = resolve_device(
    settings.audio.input_device or settings.audio.input_device_index,
    is_input=True,
)
if input_device is None:
    default_input = get_default_input_device()
    if default_input is None:
        raise AudioDeviceError(
            message="No input audio device available",
            device=None,
            suggestion="Connect a microphone and restart",
        )
```

### VAD Error Logging Fix
```python
# Current (vad.py:44-49)
except Exception:
    pass  # BAD: Swallowing errors

# Fixed
except Exception as e:
    logger.error(f"VAD is_speech error: {e}")
    # Continue processing, but error is now visible
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Bare `pass` in exception handlers | `logger.error()` with context | Phase 3 | Visibility into VAD failures |
| Pydantic ValidationError | Clean exit with actionable message | Phase 3 | User-friendly startup errors |
| Mixed stdout/stderr | Consistent stderr for errors | Phase 3 | Proper CLI behavior |

## Open Questions

1. **Should we verify models can LOAD, or just EXIST?**
   - What we know: VERF-02 says "load successfully"
   - What's unclear: Loading LLM model takes 5-10s, adds startup latency
   - Recommendation: Check existence only (VERF-01), let natural load failure handle VERF-02. Loading happens during service init with good error messages already.

2. **What order should checks run?**
   - What we know: User left order to discretion
   - What's unclear: Models vs audio first
   - Recommendation: Models first (faster check), then audio (requires device enumeration)

3. **Should we keep pydantic validators as backup?**
   - What we know: Current validators raise ValidationError
   - What's unclear: Whether to remove or keep as safety net
   - Recommendation: Keep as safety net, but primary path is startup verifier with clean exit

## Sources

### Primary (HIGH confidence)
- Python stdlib docs - `sys.exit()` behavior - https://docs.python.org/3/library/sys.html#sys.exit
- Existing codebase - `config.py`, `main.py`, `devices.py` - direct analysis
- BSD sysexits.h convention - https://man.openbsd.org/sysexits

### Secondary (MEDIUM confidence)
- Python CLI best practices - https://clig.dev/#errors
- Exit code conventions - https://tldp.org/LDP/abs/html/exitcodes.html

### Tertiary (LOW confidence)
- None for this phase - all patterns verified in codebase

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all stdlib or existing codebase
- Architecture: HIGH - patterns already established in codebase
- Pitfalls: HIGH - identified from existing code review

**Research date:** 2026-02-18
**Valid until:** 30 days (stable patterns)
