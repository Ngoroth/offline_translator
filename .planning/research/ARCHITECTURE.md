# Architecture Research

**Domain:** Offline Speech-to-Speech Translation (Async Pipeline)
**Researched:** 2026-02-18
**Confidence:** HIGH

## Existing Architecture Overview

```
+------------------------------------------------------------------+
|                         Orchestrator                              |
|  +------------------------------------------------------------+  |
|  |              TranslationPipeline                            |  |
|  |  +--------+   +--------+   +--------+   +--------+   +----------+  |
|  |  |  VAD   |-->|  STT   |-->|  LLM   |-->|  TTS   |-->| Player   |  |
|  |  | Worker |   | Worker |   | Worker |   | Worker |   | Worker   |  |
|  |  +--------+   +--------+   +--------+   +--------+   +----------+  |
|  |       |            |            |            |             |       |  |
|  |  [Queue]      [Queue]      [Queue]      [Queue]       [Queue]     |  |
|  +------------------------------------------------------------+  |
+------------------------------------------------------------------+
         |                                       |
+--------v--------+                   +----------v-----------+
| Hardware Abstraction Layer          |   Session Manager    |
|  +-------------+  +-------------+   |  +----------------+  |
|  | BaseInput   |  | AudioDev    |   |  | Session State  |  |
|  | (ABC)       |  | (Rec/Play)  |   |  | Cancel Events  |  |
|  +------+------+  +-------------+   |  +----------------+  |
|         |                          +----------------------+
|  +------+------+ +------------+ +------------+
|  | KeyboardIn  | | EvdevInput | | GPIOInput  |
|  | (Win/X11)   | | (Linux)    | | (RPi)      |
|  +-------------+ +------------+ +------------+
+----------------------------------------------+
```

### Component Responsibilities

| Component | Responsibility | Current Implementation |
|-----------|----------------|------------------------|
| **Orchestrator** | Main event loop, PTT state machine, barge-in coordination | `orchestrator.py` |
| **TranslationPipeline** | Worker task management, queue coordination, session lifecycle | `pipeline.py` |
| **VAD Worker** | Voice activity detection, silence threshold, segment harvesting | `_vad_worker()` in pipeline |
| **STT Worker** | Speech-to-text transcription with faster-whisper | `_stt_worker()` + `STTService` |
| **LLM Worker** | Translation via llama.cpp | `_llm_worker()` + `LLMService` |
| **TTS Worker** | Text-to-speech synthesis via Piper | `_tts_worker()` + `TTSService` |
| **Player Worker** | Audio playback coordination | `_player_worker()` |
| **SessionManager** | Session ID tracking, validation, cancellation | `session.py` |
| **BaseInput** | Platform-independent input abstraction | `input.py` (ABC) |
| **AudioRecorder/Player** | Platform audio I/O | `audio.py` |

## Recommended Project Structure

```
offline_translator/
+-- src/app/
|   +-- core/                    # Platform abstractions
|   |   +-- input.py             # BaseInput ABC + implementations
|   |   +-- audio.py             # AudioRecorder/Player
|   |   +-- types.py             # TypedDict payloads
|   |   +-- config.py            # Settings models
|   |   +-- logging.py           # Loguru setup
|   +-- services/                # AI model wrappers
|   |   +-- stt.py               # WhisperModel wrapper
|   |   +-- llm.py               # Llama wrapper
|   |   +-- tts.py               # Piper wrapper
|   +-- orchestrator/            # Pipeline coordination
|   |   +-- pipeline.py          # TranslationPipeline
|   |   +-- orchestrator.py      # Main event loop
|   |   +-- session.py           # Session management
|   +-- utils/                   # Shared utilities
|       +-- vad.py               # VAD + SilenceDetector
|       +-- buffers.py           # Audio buffer utilities
|   +-- main.py                  # Entry point
+-- tests/
|   +-- unit/                    # Isolated component tests
|   +-- integration/             # Service wiring tests
|   +-- e2e/                     # Full pipeline with real models
|   +-- smoke/                   # Quick initialization tests
|   +-- mocks/                   # Test doubles
|       +-- mock_audio.py        # MockAudioRecorder/Player
|       +-- mock_input.py        # MockInput for testing
|       +-- mock_gpio.py         # GPIO simulation
+-- models/                      # GGUF/ONNX models (gitignored)
+-- scripts/                     # Utility scripts
+-- config.yaml                  # Active configuration
+-- pyproject.toml
```

### Structure Rationale

- **core/**: Platform-specific code isolated behind ABCs; easy to mock for testing
- **services/**: Model wrappers are pure async with session injection; testable in isolation
- **orchestrator/**: Pipeline logic centralized; workers are private methods
- **tests/mocks/**: Test doubles extend ABCs for type safety
- **Test tiers**: unit → integration → e2e mirrors dependency depth

---

## Architectural Patterns

### Pattern 1: Producer-Consumer with Sentinel Shutdown

**What:** Workers consume from asyncio.Queue; `None` sentinel signals graceful termination.

**When to use:** Any multi-stage async pipeline where stages must complete in-order.

**Trade-offs:** 
- + Clean shutdown without race conditions
- + Backpressure handled by queue capacity
- - Sentinel must propagate through all stages

**Example (from existing codebase):**
```python
async def _stt_worker(self) -> None:
    while not self.session.cancel_event.is_set():
        payload = await self.stt_queue.get()
        
        if payload is None:  # Sentinel
            await self.llm_queue.put(None)  # Propagate
            break
        
        # Process...
```

### Pattern 2: Cooperative Cancellation with asyncio.Event

**What:** Session holds an `asyncio.Event` that workers check in their loop condition.

**When to use:** When cancellation must be graceful (cleanup resources, finish current item).

**Trade-offs:**
- + No abrupt task termination
- + Resources can be released properly
- - Requires explicit checks in all loops

**Example:**
```python
@dataclass
class Session:
    cancel_event: asyncio.Event = field(default_factory=asyncio.Event)

# In worker:
while not self.session.cancel_event.is_set():
    # Cooperative check point
```

### Pattern 3: Hardware Abstraction Layer (HAL)

**What:** Abstract base classes define interfaces; platform implementations vary.

**When to use:** Cross-platform deployment (Windows dev, RPi production).

**Trade-offs:**
- + Same tests run on all platforms with mock implementations
- + Production code unchanged between platforms
- - Additional indirection layer

**Example:**
```python
class BaseInput(ABC):
    @abstractmethod
    async def wait_for_press(self) -> Role: ...
    
    @abstractmethod
    async def wait_for_release(self, role: Role) -> None: ...

# Windows: KeyboardInput (pynput)
# Linux headless: EvdevInput (evdev)
# RPi: GPIOInput (lgpio)
```

### Pattern 4: Session-Context Injection

**What:** Services receive `session_manager` reference for cooperative cancellation.

**When to use:** Long-running AI inference that must abort on barge-in.

**Trade-offs:**
- + Models can abort early
- + Reduces latency on cancellation
- - Tighter coupling (acceptable for this use case)

**Example:**
```python
# In pipeline init:
self.stt.session_manager = self.session_manager

# In STT service:
if self.session_manager and not self.session_manager.is_valid(session_id):
    return None  # Early abort
```

---

## Data Flow

### Request Flow (PTT Press to Playback)

```
[PTT Press]
    |
    v
[Orchestrator.wait_for_press()] --> [Pipeline.start_session(role)]
    |                                        |
    |                              +---------v----------+
    |                              | Start Recorder     |
    |                              | Start VAD Worker   |
    |                              | Start STT/LLM/TTS/Player Workers |
    |                              +--------------------+
    v
[Orchestrator.wait_for_release(role)]
    |
    v
[Pipeline.handle_input_complete()]
    |
    +--> recorder.stop() --> audio buffer
    |                              |
    |                              v
    +--> stt_queue.put(audio_payload)
    |                              |
    |                              v
    |                   [STT Worker] --> text
    |                              |
    |                              v
    |                   llm_queue.put(text_payload)
    |                              |
    |                              v
    |                   [LLM Worker] --> translation
    |                              |
    |                              v
    |                   tts_queue.put(translation_payload)
    |                              |
    |                              v
    |                   [TTS Worker] --> audio chunks
    |                              |
    |                              v
    |                   player_queue.put(chunk)
    |                              |
    |                              v
    +------------------- [Player Worker] --> speaker
```

### Barge-In Flow

```
[PTT Press (during playback)]
    |
    v
[Orchestrator detects barge-in via asyncio.wait(FIRST_COMPLETED)]
    |
    v
[Pipeline.handle_barge_in()]
    |
    +--> session.cancel_event.set()  (signals all workers)
    +--> player.stop()               (immediate audio stop)
    +--> recorder.stop()
    +--> Cancel all worker tasks
    +--> Clear all queues
    +--> Start new session
```

### State Transitions

```
IDLE --> LISTENING (on PTT press)
LISTENING --> PROCESSING (on PTT release)
PROCESSING --> SPEAKING (on first audio chunk)
SPEAKING --> IDLE (on playback complete or barge-in)
```

---

## Testing Patterns for Async Pipelines

### Test Tier Architecture

| Tier | Scope | Speed | Dependencies |
|------|-------|-------|--------------|
| **Unit** | Single function/class | Fast (<1s) | All external mocked |
| **Smoke** | Initialization/ wiring | Fast (<5s) | Mocked models |
| **Integration** | Multi-component | Medium (5-30s) | Mocked inference |
| **E2E** | Full pipeline | Slow (30s+) | Real models |

### Pattern: AsyncMock for Service Dependencies

```python
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_pipeline_flow():
    mock_stt = AsyncMock()
    mock_stt.transcribe.return_value = "Hello"
    
    mock_llm = AsyncMock()
    mock_llm.translate.return_value = "Hola"
    
    # Inject mocks into pipeline
    pipeline = TranslationPipeline(
        settings=mock_settings,
        stt=mock_stt,
        llm=mock_llm,
        ...
    )
```

### Pattern: Mock Implementations Extending ABCs

```python
class MockAudioRecorder(AudioRecorder):
    def __init__(self):
        self.buffer = []
        self._queue = asyncio.Queue()
    
    def start(self) -> None:
        self.buffer = []
    
    def stop(self) -> np.ndarray:
        return self.extract_buffer()
    
    async def get_chunk(self) -> np.ndarray:
        return await self._queue.get()
    
    def inject_chunk(self, chunk: np.ndarray) -> None:
        """Test helper to simulate audio arrival."""
        self._queue.put_nowait(chunk)
```

### Pattern: Sentinel Verification in Tests

```python
@pytest.mark.asyncio
async def test_graceful_shutdown():
    pipeline = await create_test_pipeline()
    await pipeline.start_session()
    await pipeline.handle_input_complete()
    
    # Wait for completion
    await pipeline.wait_for_completion()
    
    # Verify sentinel propagated through all queues
    # (all workers should have exited cleanly)
    assert pipeline.tasks == []
```

### Pattern: Cancellation Race Testing

```python
@pytest.mark.asyncio
async def test_cancellation_aborts_slow_inference():
    # Mock slow transcribe (simulates real model latency)
    async def slow_transcribe(*args, **kwargs):
        await asyncio.sleep(2.0)  # Simulate slow inference
        return "Delayed result"
    
    mock_stt.transcribe.side_effect = slow_transcribe
    
    session = await pipeline.start_session()
    await pipeline.handle_input_complete()
    
    # Cancel mid-processing
    await asyncio.sleep(0.1)
    await pipeline.stop_session()
    
    # Verify result did NOT leak to next stage
    assert pipeline.llm_queue.empty() or \
           await pipeline.llm_queue.get() is None
```

### Pattern: Platform-Specific Test Skipping

```python
import sys
import pytest

@pytest.mark.skipif(sys.platform != "linux", reason="GPIO only on Linux")
def test_gpio_input_initialization():
    from app.core.input import GPIOInput
    # ...

@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Requires X11")
def test_keyboard_input_with_display():
    from app.core.input import KeyboardInput
    # ...
```

---

## Device Deployment Verification Strategies

### Phase 1: Local Verification (Windows)

1. **Unit Tests**: All pass with mocks
2. **Smoke Tests**: Service initialization with mock models
3. **Integration Tests**: Pipeline wiring with mock inference
4. **Type Check**: `basedpyright` passes with strict settings
5. **Lint**: `ruff check .` passes

```bash
# Local verification command
uv run basedpyright && uv run ruff check . && uv run pytest -m "not e2e"
```

### Phase 2: Cross-Platform Verification (CI/Local)

1. **Platform Detection Tests**: Verify correct input implementation selected
2. **HAL Mock Tests**: Test all platform implementations via mocks
3. **Config Loading Tests**: Verify YAML parsing on all platforms

```python
# Test that correct input is selected per platform
def test_input_selection_windows(monkeypatch):
    monkeypatch.setattr(sys, 'platform', 'win32')
    # Verify KeyboardInput selected

def test_input_selection_rpi(monkeypatch):
    monkeypatch.setattr(sys, 'platform', 'linux')
    monkeypatch.setenv('GPIO_PIN_A', '17')
    # Verify GPIOInput selected
```

### Phase 3: Target Device Verification (Raspberry Pi)

1. **GPIO Hardware Test**: Physical button response
2. **Audio Hardware Test**: Speaker/mic functionality
3. **Model Loading Test**: Verify models load on ARM
4. **Latency Test**: Measure end-to-end timing
5. **Thermal Test**: Monitor temperature under load

```bash
# On-device verification script
uv run pytest -m "smoke"              # Quick sanity check
uv run pytest -m "integration"        # With mocked inference
uv run pytest tests/e2e/ --timeout=120  # Full pipeline
```

### Phase 4: Production Readiness

1. **Stress Test**: 100+ translation cycles
2. **Barge-in Stress Test**: Rapid press/release cycles
3. **Memory Monitor**: Check for leaks over time
4. **Temperature Monitor**: Ensure thermal throttling doesn't occur

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Blocking the Event Loop

**What people do:** Call synchronous model inference directly in async worker.

**Why it's wrong:** Blocks all other workers (VAD, cancellation handling) during inference.

**Do this instead:** Use `asyncio.to_thread()` for blocking calls:

```python
# WRONG
async def _stt_worker(self):
    text = self.stt.model.transcribe(audio)  # Blocks!

# CORRECT
async def _stt_worker(self):
    text = await asyncio.to_thread(
        self.stt.model.transcribe, audio
    )
```

### Anti-Pattern 2: Queue Without Backpressure

**What people do:** Unlimited queue size, producers faster than consumers.

**Why it's wrong:** Memory grows unbounded; latency increases; eventually OOM.

**Do this instead:** Use bounded queues with `put()` timeout or `put_nowait()` + handling:

```python
# Consider bounded queues for production
self.stt_queue = asyncio.Queue(maxsize=10)
```

### Anti-Pattern 3: Missing Cancellation Check in Loops

**What people do:** Workers don't check cancel_event.

**Why it's wrong:** Barge-in doesn't stop processing; wasted compute; delayed response.

**Do this instead:** Every worker loop checks cancellation:

```python
while not self.session.cancel_event.is_set():
    payload = await self.stt_queue.get()
    # ...
```

### Anti-Pattern 4: Sentinel Not Propagated

**What people do:** Worker breaks on sentinel but doesn't forward to next stage.

**Why it's wrong:** Downstream workers hang forever waiting for input.

**Do this instead:** Always propagate sentinel:

```python
if payload is None:
    await self.llm_queue.put(None)  # Forward the sentinel
    break
```

### Anti-Pattern 5: Platform Code in Core Logic

**What people do:** `if sys.platform == 'win32':` scattered in pipeline.

**Why it's wrong:** Hard to test; violates separation of concerns.

**Do this instead:** Platform differences isolated in HAL implementations:

```python
# Core code is platform-agnostic
input_provider: BaseInput = create_input_for_platform(settings)
await input_provider.wait_for_press()
```

---

## Build Order for Verification Phases

Based on the architecture, recommended verification order:

### Phase 1: Static Verification (Fastest feedback)
1. `basedpyright` type checking
2. `ruff` linting
3. Import validation (smoke tests)

### Phase 2: Unit Tests (Mocked dependencies)
1. Core types and payloads
2. Session management
3. VAD logic
4. Config validation
5. Input abstraction (with mocks)

### Phase 3: Integration Tests (Mocked inference)
1. Pipeline wiring
2. Cancellation propagation
3. Barge-in handling
4. Multi-segment sessions
5. Dual-speaker flow

### Phase 4: E2E Tests (Real models)
1. Model loading (STT, LLM, TTS)
2. Full pipeline with synthetic audio
3. Latency benchmarking

### Phase 5: On-Device Verification
1. GPIO input test
2. Audio hardware test
3. ARM model loading
4. Thermal monitoring

---

## Sources

- **pytest-asyncio documentation**: https://pytest-asyncio.readthedocs.io/ (HIGH confidence)
- **Python asyncio documentation**: https://docs.python.org/3/library/asyncio.html (HIGH confidence)
- **pytest-mock documentation**: https://pytest-mock.readthedocs.io/ (HIGH confidence)
- **Event loop blocking detection**: https://deepankarm.github.io/posts/detecting-event-loop-blocking-in-asyncio/ (MEDIUM confidence)
- **Async pipeline patterns**: https://medium.com/@sparknp1/async-python-pipelines-that-dont-melt-down (MEDIUM confidence)
- **Hardware Abstraction Layers**: https://www.dmcinfo.com/blog/39967/why-hardware-abstraction-layers-hal-are-essential-for-scalable-test-systems (MEDIUM confidence)
- **CircuitPython mocks**: https://circuitpython-mocks.readthedocs.io/ (MEDIUM confidence)
- **Raspberry Pi deployment**: https://docs.ultralytics.com/guides/raspberry-pi/ (HIGH confidence)
- **Existing codebase analysis**: `src/app/orchestrator/`, `tests/` (HIGH confidence)

---
*Architecture research for: Offline Translator (Neuromancer Pi)*
*Researched: 2026-02-18*
