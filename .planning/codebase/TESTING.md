# Testing Patterns

**Analysis Date:** 2026-02-20

## Test Framework

**Runner:**
- pytest (version >=7.0)
- pytest-asyncio (>=1.3.0) for async test support
- Config: `pyproject.toml`

**Assertion Library:**
- Built-in `assert` statements
- No separate assertion library

**Run Commands:**
```bash
uv run pytest                        # Run all tests
uv run pytest tests/unit/            # Run unit tests only
uv run pytest -m smoke               # Run smoke tests only
uv run pytest -m "not slow"          # Skip slow tests
uv run pytest --cov=app              # Coverage (if configured)
```

## Test Organization

**Location:**
- Tests in separate `tests/` directory at project root
- Mirrors source structure under `tests/`

**Naming:**
- Test files: `test_<module>_<feature>.py` or `test_<module>.py`
- Test classes: `Test<Feature>` (PascalCase)
- Test functions: `test_<description>` (snake_case)

**Structure:**
```
tests/
├── __init__.py                  # Marks as package
├── unit/                        # Unit tests (mocked dependencies)
│   ├── test_stt.py
│   ├── test_llm.py
│   ├── test_orchestrator.py
│   └── ...
├── smoke/                       # Quick initialization tests
│   ├── conftest.py              # Shared fixtures
│   ├── test_service_initialization.py
│   └── test_pipeline_wiring.py
├── integration/                 # Service wiring tests
│   ├── test_pipeline.py
│   ├── test_barge_in.py
│   └── ...
├── e2e/                         # Full pipeline with real models
│   ├── conftest.py              # Model download fixtures
│   └── test_golden_path.py
└── mocks/                       # Test doubles
    ├── mock_audio.py
    ├── mock_input.py
    └── mock_gpio.py
```

## Test Markers

**Defined in `pyproject.toml`:**
```toml
[tool.pytest.ini_options]
markers = [
    "smoke: Quick initialization tests (mocked models)",
    "integration: Service wiring tests (mocked inference)",
    "e2e: Full pipeline with real models (requires downloads)",
    "benchmark: Performance tests (NFR validation)",
    "slow: Tests taking > 30s",
]
```

**Usage:**
```python
@pytest.mark.asyncio
@pytest.mark.smoke
async def test_service_init():
    ...

@pytest.mark.e2e
@pytest.mark.slow
class TestGoldenPath:
    ...
```

## Test Structure

**Suite Organization:**
```python
# Simple test function
def test_silence_detector_timeout() -> None:
    detector = SilenceDetector(threshold_ms=500, sample_rate=16000)
    assert detector.is_silent_timeout(is_speech=False, num_samples=4000) is False

# Test class for grouping related tests
class TestGoldenPath:
    @pytest.mark.asyncio
    async def test_stt_with_real_whisper_model(self, stt_model_path, synthetic_audio_generator):
        ...

# Async test with fixtures
@pytest.mark.asyncio
async def test_stt_transcribe_async(mock_whisper: MagicMock, stt_settings: STTSettings) -> None:
    ...
```

**Patterns:**
- Setup: Use fixtures for reusable setup
- Teardown: Fixtures handle cleanup automatically
- Assertion: Direct assert statements with descriptive messages

## Mocking

**Framework:** `unittest.mock` (MagicMock, AsyncMock, patch)

**Patterns:**

**Patching External Dependencies:**
```python
@pytest.mark.asyncio
@patch("app.services.stt.WhisperModel")
async def test_stt_transcribe_async(mock_whisper: MagicMock, stt_settings: STTSettings) -> None:
    mock_model_instance = mock_whisper.return_value
    mock_segment = MagicMock()
    mock_segment.text = "Hello world"
    mock_info = MagicMock()
    mock_info.language = "en"
    mock_model_instance.transcribe.return_value = ([mock_segment], mock_info)
    ...
```

**Mocking Async Methods:**
```python
mock_stt = AsyncMock()
mock_stt.transcribe.return_value = "Hello"

# Or with side_effect for async generators
async def slow_tts(*_args, **_kwargs):
    for _ in range(10):
        yield b"\x00" * 100
        await asyncio.sleep(0.05)

mock_tts.synthesize.side_effect = slow_tts
```

**What to Mock:**
- External AI model inference (WhisperModel, Llama, PiperVoice)
- Hardware interfaces (GPIO, audio devices)
- File system operations (with tmp_path fixture)
- Network operations

**What NOT to Mock:**
- Business logic (test directly)
- Data transformations (test directly)
- Simple utility functions (test directly)

## Fixtures and Factories

**Test Data:**
```python
# Simple fixture
@pytest.fixture
def stt_settings() -> STTSettings:
    return STTSettings(
        model_path="tiny",
        language="en",
        beam_size=5,
        device="cpu",
        compute_type="int8"
    )

# Fixture with tmp_path
@pytest.fixture
def mock_llm_model_path(tmp_path: Path) -> str:
    model_path = tmp_path / "mock_model.gguf"
    model_path.touch()
    return str(model_path)

# Session-scoped fixture (for expensive resources)
@pytest.fixture(scope="session")
def stt_model_path() -> Path:
    return Path(snapshot_download(
        repo_id=STT_REPO,
        cache_dir=CACHE_DIR,
    ))

# Factory fixture
@pytest.fixture
def synthetic_audio_generator():
    def _create(duration_seconds: float = 1.0, sample_rate: int = 16000) -> np.ndarray:
        t = np.linspace(0, duration_seconds, int(sample_rate * duration_seconds))
        audio = 0.5 * np.sin(2 * np.pi * 150 * t) + np.random.randn(len(t)) * 0.05
        return audio.astype(np.float32)
    return _create
```

**Location:**
- Shared fixtures in `conftest.py` files
- Test-specific fixtures in test files
- Mock implementations in `tests/mocks/`

## Mock Implementations

**Pattern from `tests/mocks/mock_input.py`:**
```python
class MockInput(BaseInput):
    """Mock input handler for testing. Allows manual triggering of press and release events."""

    def __init__(self):
        self.pressed_state: dict[Role, bool] = {"a": False, "b": False}
        self._press_queue: asyncio.Queue[Role] = asyncio.Queue()
        self._release_events: dict[Role, asyncio.Event] = {
            "a": asyncio.Event(),
            "b": asyncio.Event(),
        }

    def trigger_press(self, role: Role):
        self.pressed_state[role] = True
        self._release_events[role].clear()
        self._press_queue.put_nowait(role)

    @override
    async def wait_for_press(self) -> Role:
        return await self._press_queue.get()
```

**Pattern from `tests/mocks/mock_audio.py`:**
```python
@final
class MockAudioRecorder(AudioRecorder):
    """Mock audio recorder for testing. Allows injecting predefined audio chunks."""

    def inject_chunk(self, chunk: NDArray[np.float32]) -> None:
        """Simulate audio data arrival."""
        if self.recording:
            self.buffer.append(chunk)
            self._queue.put_nowait(chunk)
```

## Coverage

**Requirements:** No explicit coverage target enforced

**View Coverage:**
```bash
uv run pytest --cov=app --cov-report=html
```

## Test Types

**Unit Tests:**
- Location: `tests/unit/`
- Scope: Single function/class with mocked dependencies
- Focus: Logic correctness, error handling, edge cases
- Example: `test_vad.py` - tests VADService with mocked webrtcvad

**Integration Tests:**
- Location: `tests/integration/`
- Scope: Multiple components working together
- Focus: Service wiring, message passing, cancellation
- Example: `test_barge_in.py` - tests orchestrator + pipeline + input

**E2E Tests:**
- Location: `tests/e2e/`
- Scope: Full pipeline with real models
- Focus: Golden path validation, performance benchmarks
- Requires: Model downloads (~535MB, cached in `~/.cache/offline_translator_tests/`)
- Example: `test_golden_path.py` - real Whisper, Qwen, Piper models

## Common Patterns

**Async Testing:**
```python
@pytest.mark.asyncio
async def test_async_operation():
    result = await service.transcribe(audio_data)
    assert result is not None
```

**Error Testing:**
```python
@pytest.mark.asyncio
async def test_stt_model_load_error(mock_whisper: MagicMock, stt_settings: STTSettings) -> None:
    mock_whisper.side_effect = Exception("Model not found")
    stt_service = STTService(stt_settings)
    audio_data = np.zeros(16000, dtype=np.float32)
    
    with pytest.raises(STTModelLoadError):
        await stt_service.transcribe(audio_data)
```

**Cancellation Testing:**
```python
@pytest.mark.asyncio
async def test_stt_transcribe_cancelled(mock_whisper: MagicMock, stt_settings: STTSettings) -> None:
    mock_session_manager = MagicMock()
    mock_session_manager.is_valid.return_value = False
    
    stt_service = STTService(stt_settings, session_manager=mock_session_manager)
    audio_data = np.zeros(16000, dtype=np.float32)
    
    result = await stt_service.transcribe(audio_data, session_id="cancelled-session")
    assert result is None
    mock_whisper.return_value.transcribe.assert_not_called()
```

**Performance Testing:**
```python
@pytest.mark.asyncio
async def test_stt_performance_benchmark(mock_whisper: MagicMock, stt_settings: STTSettings) -> None:
    # Setup mock...
    stt_service = STTService(stt_settings)
    audio_data = np.zeros(80000, dtype=np.float32)  # 5 seconds
    
    start_time = time.time()
    text = await stt_service.transcribe(audio_data)
    end_time = time.time()
    
    transcription_time = end_time - start_time
    assert transcription_time < 1.0, f"Transcription took {transcription_time:.2f}s, expected < 1.0s"
```

**Integration Test with Task Management:**
```python
@pytest.mark.asyncio
async def test_orchestrator_loop_flow(orchestrator, mock_deps) -> None:
    mock_deps["input"].wait_for_press.side_effect = ["a", asyncio.CancelledError]
    mock_deps["input"].wait_for_release.return_value = None
    
    try:
        await orchestrator.run()
    except asyncio.CancelledError:
        pass
    
    mock_deps["pipeline"].start_session.assert_called()
    mock_deps["input"].wait_for_release.assert_called_with("a")
```

## Pytest Configuration

**From `pyproject.toml`:**
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
```

- `asyncio_mode = "auto"`: Automatically handles async tests without explicit `@pytest_asyncio.fixture`
- `asyncio_default_fixture_loop_scope = "function"`: Each test gets its own event loop

---

*Testing analysis: 2026-02-20*
