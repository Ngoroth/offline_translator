# Coding Conventions

**Analysis Date:** 2026-02-17

## Naming Patterns

**Files:**
- Snake_case for all Python files: `test_stt.py`, `pipeline.py`, `orchestrator.py`
- Test files prefix with `test_`: `test_vad.py`, `test_llm.py`
- Mock files in `tests/mocks/`: `mock_audio.py`, `mock_input.py`

**Classes:**
- PascalCase for class names: `STTService`, `LLMService`, `TranslationPipeline`
- Service classes end with `Service`: `VADService`, `TTSService`
- Exception classes end with `Error`: `LLMError`, `STTModelLoadError`
- Test classes use PascalCase with descriptive names: `TestSTTServiceInit`, `TestGoldenPath`

**Functions:**
- Snake_case for all functions: `transcribe()`, `translate()`, `start_session()`
- Private methods prefix with underscore: `_init_model()`, `_vad_worker()`
- Async functions use `async def`: `async def translate()`, `async def transcribe()`
- Test functions prefix with `test_`: `test_translate_success()`, `test_stt_initialization()`

**Variables:**
- Snake_case: `sample_rate`, `source_lang`, `session_id`
- Type hints are mandatory in source code (per `basedpyright` strict mode)
- Constants use UPPER_SNAKE_CASE in module scope: `CACHE_DIR`, `STT_REPO`
- Private instance variables prefix with underscore: `self._model`, `self._lock`

**Types:**
- Type aliases in PascalCase: `AudioPayload`, `TextPayload`, `Role`
- Use `typing.Final` for immutable classes: `@final class LLMService`
- Use `typing.override` when overriding: `@override def start()`

## Code Style

**Formatting:**
- **Tool:** Ruff (configured in `pyproject.toml`)
- **Line length:** 100 characters
- **Target version:** Python 3.12

**Linting:**
- **Tool:** Ruff for linting, basedpyright for type checking
- **Strict type checking** enforced in `src/` (see `pyproject.toml`)
- Tests have relaxed type checking rules

**Import Organization:**
```python
# 1. Standard library imports
import asyncio
import time
from pathlib import Path
from typing import cast, final, TYPE_CHECKING

# 2. Third-party imports
import numpy as np
from loguru import logger
from pydantic import BaseModel, Field

# 3. Local application imports
from app.core.config import LLMSettings
from app.core.types import AudioPayload
```

**Path Aliases:**
- No special path aliases configured
- Imports use absolute paths from project root: `from app.services.stt import STTService`

## Error Handling

**Patterns:**

1. **Service-Level Exceptions:** Each service defines its own exception hierarchy
   ```python
   class LLMError(Exception):
       """Base exception for LLM service errors."""
       pass

   class LLMModelLoadError(LLMError):
       """Raised when the model fails to load."""
       pass
   ```

2. **Try/Except with Logging:** Always log errors before raising or returning
   ```python
   try:
       self._model = Llama(...)
   except Exception as e:
       logger.error(f"Failed to load LLM model: {e}")
       raise LLMModelLoadError(...) from e
   ```

3. **Graceful Degradation:** Use `pass` for non-critical errors
   ```python
   try:
       if self.vad.is_speech(chunk, self.sample_rate):
           has_speech = True
   except Exception:
       pass  # Continue processing
   ```

4. **Session Cancellation:** Check session validity before operations
   ```python
   if session_id and self.session_manager and not self.session_manager.is_valid(session_id):
       logger.debug(f"LLM: Pre-check cancelled for session {session_id}")
       return None
   ```

## Logging

**Framework:** loguru

**Patterns:**

1. **Module-level logger usage:**
   ```python
   from loguru import logger
   
   logger.info(f"Loading LLM model from {self.settings.model_path}")
   logger.error(f"Translation failed: {e}")
   logger.debug("VAD Worker started")
   ```

2. **Performance timing:**
   ```python
   start_time = time.perf_counter()
   # ... operation ...
   load_time = time.perf_counter() - start_time
   logger.info(f"LLM model loaded in {load_time:.2f}s")
   ```

3. **Log Levels:**
   - `INFO`: Important state changes, completions
   - `DEBUG`: Detailed flow information
   - `ERROR`: Failures and exceptions
   - `WARNING`: Non-critical issues

**Configuration:**
- Console output: Human-readable format with colors
- File output: JSON format with rotation (10 MB), retention (1 week)
- See `src/app/core/logging.py` for full configuration

## Type Safety

**Strict Requirements (src/ only):**

1. **All functions must have return type annotations:**
   ```python
   async def translate(self, text: str, ...) -> str | None:
   def is_speech(self, audio_data: np.ndarray[tuple[int], np.dtype[np.float32]]) -> bool:
   ```

2. **All parameters must have type annotations:**
   ```python
   def __init__(self, settings: LLMSettings, session_manager: "SessionManager | None" = None) -> None:
   ```

3. **Use TYPE_CHECKING for circular imports:**
   ```python
   from typing import TYPE_CHECKING
   if TYPE_CHECKING:
       from app.orchestrator.session import SessionManager
   ```

4. **Cast when necessary:**
   ```python
   from typing import cast
   resp_typed = cast(CreateChatCompletionResponse, response)
   ```

5. **Generic numpy arrays:**
   ```python
   def process_audio(self, audio: np.ndarray[tuple[int], np.dtype[np.float32]]) -> None:
   ```

## Function Design

**Size:**
- Functions should be focused and single-purpose
- Worker functions (`_stt_worker()`, `_vad_worker()`) are longer but well-organized with clear sections

**Parameters:**
- Use dataclasses/pydantic models for complex configuration (e.g., `LLMSettings`, `AppSettings`)
- Optional parameters use `| None` syntax: `session_id: str | None = None`
- Prefer explicit parameters over `**kwargs`

**Return Values:**
- Return `None` for operations that may be cancelled: `-> str | None`
- Return typed payloads for structured data: `-> AudioPayload`
- Use exceptions for error cases, not error return codes

## Module Design

**Exports:**
- No explicit `__all__` declarations found
- Public API is determined by what's imported in `__init__.py` files

**Barrel Files:**
- `src/app/core/__init__.py` appears minimal
- Direct imports preferred: `from app.core.config import LLMSettings`

## Async Patterns

**Guidelines:**

1. **Mark async functions clearly:**
   ```python
   @pytest.mark.asyncio
   async def test_translate_success(...) -> None:
   ```

2. **Offload blocking operations to threads:**
   ```python
   response = await asyncio.to_thread(
       self._model.create_chat_completion,
       messages=messages,
       temperature=0.1,
   )
   ```

3. **Use locks for shared resources:**
   ```python
   self._lock: asyncio.Lock = asyncio.Lock()
   async with self._lock:
       response = await asyncio.to_thread(...)
   ```

4. **Properly handle cancellation:**
   ```python
   try:
       await self.completion_task
   except asyncio.CancelledError:
       pass
   ```

## Comments

**When to Comment:**
- Complex logic sections in worker functions
- TODO comments for future improvements (with context)
- Performance-related notes

**JSDoc/TSDoc:**
- Not applicable (Python project)
- Use docstrings for classes and public methods

**Docstring Format:**
```python
class VADService:
    """Voice Activity Detection using WebRTC VAD."""
    
    def is_speech(self, audio_data: ...) -> bool:
        """
        Returns True if the audio frame contains speech.
        Expects float32 array, converts to int16 for WebRTC VAD.
        """
```

---

*Convention analysis: 2026-02-17*
