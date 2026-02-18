# Testing Patterns

**Analysis Date:** 2026-02-17

## Test Framework

**Runner:**
- **Framework:** pytest 7.0+
- **Async testing:** pytest-asyncio 0.23.0+
- **Config location:** `pyproject.toml` (lines 81-91)

**Configuration:**
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
markers = [
    "smoke: Quick initialization tests (mocked models)",
    "integration: Service wiring tests (mocked inference)",
    "e2e: Full pipeline with real models (requires downloads)",
    "benchmark: Performance tests (NFR validation)",
    "slow: Tests taking > 30s",
]
```

**Assertion Library:**
- Built-in pytest assertions
- NumPy testing utilities where needed: `np.testing.assert_array_equal`

**Run Commands:**
```bash
# Run all tests
uv run pytest

# Run by marker
uv run pytest -m smoke
uv run pytest -m integration
uv run pytest -m e2e

# Run specific test file
uv run pytest tests/unit/test_llm.py

# Run with coverage
uv run pytest --cov=src
```

## Test File Organization

**Location:**
- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/`
- Smoke tests: `tests/smoke/`
- E2E tests: `tests/e2e/`
- Shared mocks: `tests/mocks/`

**Naming:**
- All test files: `test_*.py`
- Test functions: `test_<description>`
- Test classes: `Test<Component><Scenario>`

**Structure:**
```
tests/
├── conftest.py              # Root conftest (not present, using per-directory)
├── mocks/                   # Shared mock implementations
│   ├── mock_audio.py
│   ├── mock_input.py
│   └── mock_gpio.py
├── unit/                    # Component tests
│   ├── conftest.py         # Not present
│   └── test_*.py           # Individual test files
├── integration/             # Integration tests
│   └── test_*.py
├── smoke/                   # Quick smoke tests
│   ├── conftest.py         # Shared fixtures for smoke tests
│   └── test_*.py
└── e2e/                     # End-to-end tests
    ├── conftest.py         # Model download fixtures
    └── test_*.py
```

## Test Structure

**Suite Organization:**
```python
import pytest
from unittest.mock import MagicMock, patch
from app.core.config import LLMSettings
from app.services.llm import LLMService


# Fixtures at module level
@pytest.fixture
def mock_settings() -> LLMSettings:
    return LLMSettings(model_path="models/test.gguf", context_window=2048, n_threads=4)


@pytest.fixture
def mock_llama():
    with patch("app.services.llm.Llama") as mock:
        yield mock


# Test class for grouping related tests
@pytest.mark.asyncio
class TestLLMServiceInit:
    """Tests for LLM service initialization."""

    async def test_llm_initialization(self, mock_settings, mock_llama):
        service = LLMService(mock_settings)
        assert getattr(service, "_model") is not None
        mock_llama.assert_called_once_with(...)
```

**Patterns:**

1. **Async test marking:**
   ```python
   @pytest.mark.asyncio
   async def test_async_operation() -> None:
       result = await service.transcribe(audio)
       assert result == "expected"
   ```

2. **Patch decorator stacking (outer first):**
   ```python
   @pytest.mark.asyncio
   @patch("app.services.tts.PiperVoice.load")
   @patch("app.services.llm.Llama")
   @patch("app.services.stt.WhisperModel")
   async def test_pipeline(mock_whisper, mock_llama, mock_piper):
       # Patches are passed in reverse order of decorators
       ...
   ```

3. **Using tmp_path for files:**
   ```python
   async def test_with_files(tmp_path: Path) -> None:
       model_path = tmp_path / "model.gguf"
       model_path.touch()
       ...
   ```

4. **Side effects for sequences:**
   ```python
   mock_deps["input"].wait_for_press.side_effect = ["a", asyncio.CancelledError]
   ```

## Mocking

**Framework:** unittest.mock (standard library)

**Patterns:**

1. **Patch external dependencies:**
   ```python
   @patch("app.services.stt.WhisperModel")
   async def test_stt(mock_whisper: MagicMock) -> None:
       mock_model = mock_whisper.return_value
       mock_model.transcribe.return_value = ([mock_segment], mock_info)
       ...
   ```

2. **Create mock fixtures:**
   ```python
   @pytest.fixture
   def mock_session_manager():
       mock = MagicMock()
       mock.is_valid.return_value = False
       return mock
   ```

3. **Mock model classes in conftest:**
   ```python
   @pytest.fixture
   def mock_whisper_model():
       mock = MagicMock()
       mock.transcribe.return_value = (
           iter([MagicMock(text="Hello world")]),
           MagicMock(language="en", language_probability=0.99),
       )
       return mock
   ```

4. **Patch with context manager:**
   ```python
   with patch("app.services.llm.Llama") as mock:
       yield mock
   ```

**What to Mock:**
- External ML models (Whisper, Llama, Piper)
- Hardware I/O (audio devices, GPIO)
- Network operations
- File system (use tmp_path)

**What NOT to Mock:**
- Internal data structures
- Pure functions
- Configuration objects (use real instances)

## Fixtures and Factories

**Test Data:**

1. **Settings fixtures (smoke/conftest.py):**
   ```python
   @pytest.fixture
   def stt_settings(mock_stt_model_path: str) -> STTSettings:
       return STTSettings(
           model_path=mock_stt_model_path,
           language="en",
           device="cpu",
           compute_type="int8",
       )
   ```

2. **Model path fixtures:**
   ```python
   @pytest.fixture
   def mock_stt_model_path(tmp_path: Path) -> str:
       model_dir = tmp_path / "mock_whisper_model"
       model_dir.mkdir(parents=True, exist_ok=True)
       return str(model_dir)
   ```

3. **Factory fixtures for data generation:**
   ```python
   @pytest.fixture
   def synthetic_audio_generator():
       def _create(duration_seconds: float = 1.0, sample_rate: int = 16000):
           t = np.linspace(0, duration_seconds, int(sample_rate * duration_seconds))
           audio = 0.5 * np.sin(2 * np.pi * 150 * t) + ...
           return audio.astype(np.float32)
       return _create
   ```

4. **Session-scoped fixtures for expensive resources:**
   ```python
   @pytest.fixture(scope="session")
   def stt_model_path() -> Path:
       return Path(snapshot_download(repo_id=STT_REPO, cache_dir=CACHE_DIR))
   ```

**Location:**
- Shared fixtures: `tests/smoke/conftest.py`, `tests/e2e/conftest.py`
- Local fixtures: Top of individual test files

## Coverage

**Requirements:** Not explicitly configured in pyproject.toml

**View Coverage:**
```bash
uv run pytest --cov=src --cov-report=html
uv run pytest --cov=src --cov-report=term-missing
```

**Coverage areas:**
- Unit tests: Component-level coverage
- Integration tests: Service wiring coverage
- E2E tests: Full pipeline coverage

## Test Types

**Unit Tests:**
- Location: `tests/unit/`
- Scope: Individual classes/functions
- Mocks: Heavy use of mocking
- Speed: Fast (< 1s each)
- Example: `test_vad.py`, `test_llm.py`

**Integration Tests:**
- Location: `tests/integration/`
- Scope: Service interactions
- Mocks: External models only
- Speed: Medium (~5-10s)
- Example: `test_pipeline.py`

**Smoke Tests:**
- Location: `tests/smoke/`
- Scope: Initialization and wiring
- Mocks: All external dependencies
- Speed: Fast (~5s total)
- Marker: `@pytest.mark.smoke`

**E2E Tests:**
- Location: `tests/e2e/`
- Scope: Full pipeline with real models
- Mocks: Minimal (only hardware I/O)
- Speed: Slow (requires model downloads, ~30s+)
- Marker: `@pytest.mark.e2e`, `@pytest.mark.slow`
- Requirements: Model downloads via Hugging Face (~535MB)

## Common Patterns

**Async Testing:**
```python
@pytest.mark.asyncio
async def test_async_operation() -> None:
    result = await service.transcribe(audio_data)
    assert result == "Hello world"
```

**Error Testing:**
```python
@pytest.mark.asyncio
async def test_translate_failure(mock_settings, mock_llama) -> None:
    service = LLMService(mock_settings)
    mock_instance = mock_llama.return_value
    mock_instance.create_chat_completion.side_effect = Exception("Inference failed")
    
    with pytest.raises(LLMError):
        await service.translate("Hello", "en", "es")
```

**Performance Testing:**
```python
@pytest.mark.asyncio
async def test_stt_performance_benchmark(mock_whisper, stt_settings) -> None:
    stt_service = STTService(stt_settings)
    audio_data = np.zeros(80000, dtype=np.float32)
    
    start_time = time.time()
    text = await stt_service.transcribe(audio_data)
    end_time = time.time()
    
    transcription_time = end_time - start_time
    assert transcription_time < 1.0
```

**Test Dependencies:**
```python
@pytest.mark.asyncio
async def test_full_pipeline(
    stt_model_path: Path,  # From e2e/conftest.py
    llm_model_path: Path,
    tts_model_path: Path,
    synthetic_audio_generator: Callable[..., np.ndarray],
):
    stt = STTService(STTSettings(model_path=str(stt_model_path)))
    ...
```

## Test Markers

**Available markers:**
- `@pytest.mark.smoke` - Quick initialization tests
- `@pytest.mark.integration` - Service wiring tests
- `@pytest.mark.e2e` - Full pipeline with real models
- `@pytest.mark.benchmark` - Performance validation
- `@pytest.mark.slow` - Tests > 30s

**Running by marker:**
```bash
# Exclude slow tests
uv run pytest -m "not slow"

# Run only smoke tests
uv run pytest -m smoke

# Run smoke and integration
uv run pytest -m "smoke or integration"
```

---

*Testing analysis: 2026-02-17*
