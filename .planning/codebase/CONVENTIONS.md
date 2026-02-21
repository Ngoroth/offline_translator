# Coding Conventions

**Analysis Date:** 2026-02-20

## Naming Patterns

**Files:**
- Snake_case: `audio_recorder.py`, `session_manager.py`, `test_barge_in.py`
- Module names are lowercase with underscores
- Test files follow pattern: `test_<module>_<feature>.py` (e.g., `test_stt_language_propagation.py`)

**Functions:**
- Snake_case for all functions and methods: `start_session()`, `handle_barge_in()`, `get_default_input_device()`
- Private methods prefixed with underscore: `_get_model()`, `_run_transcription()`, `_read_stdout()`
- Async functions use `async def` without special naming suffix

**Variables:**
- Snake_case: `audio_data`, `session_id`, `sample_rate`
- Private instance attributes prefixed with underscore: `_model`, `_lock`, `_queue`
- Constants are UPPER_SNAKE_CASE: `STT_REPO`, `CACHE_DIR`, `TTS_FOLDER`

**Types:**
- PascalCase for classes: `STTService`, `TranslationPipeline`, `AudioDeviceError`
- Exception classes suffixed with `Error`: `STTError`, `LLMError`, `AudioDeviceError`
- TypedDict classes suffixed with `Payload`: `AudioPayload`, `TextPayload`, `TranslationPayload`
- Protocol classes suffixed with `Proto`: `PiperVoiceProto`, `PiperConfigProto`
- Settings classes suffixed with `Settings`: `STTSettings`, `LLMSettings`, `AudioSettings`

**Type Aliases:**
- Simple types use PascalCase: `Role = Literal["a", "b"]`, `EventType = Literal["press", "release"]`

## Code Style

**Formatting:**
- Ruff linter/formatter with line length 100
- Target version: Python 3.12
- Config in `pyproject.toml`:
  ```toml
  [tool.ruff]
  line-length = 100
  target-version = "py312"
  ```

**Linting:**
- Ruff for linting and formatting
- Strict type checking with basedpyright
- No `# noqa` or `# type: ignore` allowed (per AGENTS.md)

## Import Organization

**Order:**
1. Standard library imports (alphabetically)
2. Third-party imports (alphabetically)
3. Local application imports (alphabetically)

**Example from `src/app/main.py`:**
```python
import asyncio  # Standard library

from loguru import logger  # Third-party

from app.core.audio import AudioPlayer, AudioRecorder  # Local imports
from app.core.config import AppSettings, load_settings
from app.services.stt import STTService
```

**Path Aliases:**
- Uses `app.` prefix for absolute imports from `src/app/`
- Example: `from app.core.config import STTSettings`
- No relative imports in source code

**TYPE_CHECKING Pattern:**
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.orchestrator.session import SessionManager
```
Used to avoid circular imports while maintaining type safety.

## Error Handling

**Custom Exceptions:**
- Create exception hierarchy with base exception per domain
- Example from `src/app/services/stt.py`:
```python
class STTError(Exception):
    """Base exception for STT service errors."""
    pass

class STTModelLoadError(STTError):
    """Raised when the model fails to load."""
    pass

class STTTranscriptionError(STTError):
    """Raised when transcription fails."""
    pass
```

**Exception with Context:**
- Use `from e` to preserve exception chain:
```python
except Exception as e:
    logger.error("Failed to load model: {}", e)
    raise STTModelLoadError(f"Failed to load model from {path}") from e
```

**Actionable Exceptions:**
- `AudioDeviceError` includes actionable suggestion:
```python
class AudioDeviceError(Exception):
    message: str
    device: str | int | None
    suggestion: str
```

**Graceful Degradation:**
- Services return `None` on cancellation rather than raising
- Session validity checked before expensive operations:
```python
if session_id and self.session_manager and not self.session_manager.is_valid(session_id):
    return None
```

## Logging

**Framework:** Loguru

**Patterns:**
- Use structured logging with context:
```python
logger.info("Configuration loaded", config=settings.model_dump(mode="json"))
logger.debug(f"STT: Pre-check cancelled for session {session_id}")
```

- Log levels by purpose:
  - `logger.info()` for significant events: session start, model load, translations
  - `logger.debug()` for detailed flow: worker starts, cancellations
  - `logger.warning()` for recoverable issues: missing model, empty audio
  - `logger.error()` for failures with exception context

**Setup:**
- `src/app/core/logging.py` configures:
  - Console sink with colored format
  - File sink with JSON format, rotation, retention
  - Must be called first in application startup

## Comments

**When to Comment:**
- Docstrings for all public classes and methods
- Inline comments for non-obvious logic or workarounds
- TODO comments for future improvements

**JSDoc/TSDoc:**
- Use Google-style docstrings:
```python
async def transcribe(
    self, audio: np.ndarray, language: str | None = None, session_id: str | None = None
) -> str | None:
    """
    Transcribe 16kHz mono float32 audio to text.

    Args:
        audio: Numpy array of audio samples.
        language: Target language code (e.g., "en", "ru"). If None, uses default.
        session_id: Optional session ID to check for cancellation.

    Returns:
        The gathered transcribed text, or None if cancelled.

    Raises:
        STTTranscriptionError: If transcription fails.
    """
```

## Function Design

**Size:** Functions typically 10-50 lines; larger functions split into helpers

**Parameters:**
- Use typed parameters with defaults where appropriate
- `| None` union type for optional parameters
- Settings objects passed as typed dataclasses

**Return Values:**
- Explicit return types with `-> Type | None`
- Async generators for streaming: `AsyncGenerator[bytes, None]`
- Return `None` for cancellation/invalid cases

**Override Pattern:**
- Use `@override` decorator from `typing` for subclass methods:
```python
from typing import override

@override
def start(self) -> None:
    ...
```

## Module Design

**Exports:**
- Explicit imports in `__init__.py` files
- Empty `__init__.py` allowed (just marks package)

**Barrel Files:**
- `__init__.py` files are minimal or empty
- Direct imports preferred: `from app.core.config import STTSettings`

**Class Design:**
- Use `@final` decorator for classes not meant to be subclassed:
```python
from typing import final

@final
class LLMService:
    ...
```

- Use `@dataclass` for data containers:
```python
@dataclass
class Session:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state: SessionState = SessionState.IDLE
```

- Use `Enum` for state machines:
```python
class SessionState(Enum):
    IDLE = auto()
    LISTENING = auto()
    PROCESSING = auto()
    SPEAKING = auto()
```

## Async Patterns

**Thread Offloading:**
- CPU-bound operations use `asyncio.to_thread()`:
```python
self._model = await asyncio.to_thread(
    WhisperModel,
    self.settings.model_path,
    device=self.settings.device,
)
```

**Locking:**
- Use `asyncio.Lock` for shared resources:
```python
self._lock: asyncio.Lock = asyncio.Lock()
async with self._lock:
    # Critical section
```

**Cancellation:**
- Check `asyncio.CancelledError` explicitly
- Clean up resources in exception handler:
```python
except asyncio.CancelledError:
    logger.debug("Worker cancelled")
    raise
```

## Pydantic Patterns

**Settings Classes:**
- Inherit from `BaseModel` for validation:
```python
class STTSettings(BaseModel):
    model_path: str = Field(..., min_length=1)
    language: str = "en"
    beam_size: int = Field(default=5, ge=1)
```

**Validators:**
- Use `@field_validator` and `@model_validator`:
```python
@field_validator("model_path")
@classmethod
def validate_model_path(cls, v: str) -> str:
    if not v.endswith(".gguf"):
        raise ValueError("Model path must end with .gguf")
    return v
```

---

*Convention analysis: 2026-02-20*
