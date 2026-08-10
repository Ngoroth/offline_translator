import pytest
import asyncio
import time
import numpy as np
from unittest.mock import MagicMock, AsyncMock
from typing import override, Any
from app.orchestrator.orchestrator import Orchestrator
from app.orchestrator.pipeline import TranslationPipeline
from app.core.input import BaseInput, Role
from app.core.audio import AudioPlayer


class MockInput(BaseInput):
    press_queue: asyncio.Queue[Role]
    release_event: asyncio.Event

    def __init__(self):
        self.press_queue = asyncio.Queue()
        self.release_event = asyncio.Event()
        self.release_event.set()

    @override
    async def wait_for_press(self) -> Role:
        return await self.press_queue.get()

    @override
    async def wait_for_release(self, role: Role) -> None:
        await self.release_event.wait()

    @override
    def start(self) -> None:
        pass

    @override
    def stop(self) -> None:
        pass

    async def trigger_press(self, role: Role) -> None:
        await self.press_queue.put(role)
        self.release_event.clear()

    async def trigger_release(self, _role: Role) -> None:
        self.release_event.set()


@pytest.fixture
def mock_settings() -> MagicMock:
    s = MagicMock()
    s.speakers = {
        "a": MagicMock(from_lang="en", to_lang="ru", tts_model="voice_ru"),
        "b": MagicMock(from_lang="ru", to_lang="en", tts_model="voice_en"),
    }
    s.vad = MagicMock()
    s.vad.aggressiveness = 3
    s.vad.threshold_ms = 500
    s.audio = MagicMock()
    s.audio.sample_rate = 16000
    return s


@pytest.mark.asyncio
async def test_barge_in_integration(mock_settings: MagicMock) -> None:
    # Components
    mock_stt = AsyncMock()
    mock_llm = AsyncMock()
    mock_tts = MagicMock()  # TTS returns async gen
    mock_recorder = MagicMock()

    # Mock get_chunk to not busy-loop
    async def get_chunk_mock() -> np.ndarray[Any, np.dtype[np.float32]]:
        await asyncio.sleep(0.01)
        return np.zeros(1600, dtype=np.float32)

    mock_recorder.get_chunk.side_effect = get_chunk_mock
    mock_recorder.start = MagicMock()
    mock_recorder.stop = MagicMock()

    mock_player = MagicMock(spec=AudioPlayer)

    # Capture when stop() is called to measure latency
    stop_timestamp = 0.0

    def stop_side_effect():
        nonlocal stop_timestamp
        stop_timestamp = time.time()

    mock_player.stop.side_effect = stop_side_effect

    # Mock TTS synthesize to "hang" or stream slowly to simulate playback time
    async def slow_tts(*_args: Any, **_kwargs: Any):
        # Yield some chunks
        for _ in range(10):
            yield b"\x00" * 100
            await asyncio.sleep(0.05)  # Simulate processing/playback time

    mock_tts.synthesize.side_effect = slow_tts

    # Pipeline
    pipeline = TranslationPipeline(
        settings=mock_settings,
        stt=mock_stt,
        llm=mock_llm,
        tts=mock_tts,
        recorder=mock_recorder,
        player=mock_player,
    )

    # Input
    input_provider = MockInput()

    # Orchestrator
    orchestrator = Orchestrator(pipeline=pipeline, input_provider=input_provider)

    # Run Orchestrator in a task
    orch_task = asyncio.create_task(orchestrator.run())

    # 1. Start Session 1
    await input_provider.trigger_press("a")
    await asyncio.sleep(0.01)  # Let orchestrator pick it up
    await input_provider.trigger_release("a")

    # We need to manually feed stt result if mocks don't do it?
    mock_stt.transcribe.return_value = "Hello"
    mock_llm.translate.return_value = "Hola"
    mock_recorder.stop.return_value = np.zeros(1600, dtype=np.float32)  # Valid audio

    # Wait for session to be active
    for _ in range(10):
        if pipeline.session and pipeline.session.state:
            break
        await asyncio.sleep(0.01)

    assert pipeline.session is not None
    session_id_1 = pipeline.session.session_id

    # Wait a bit for it to progress to TTS/Player
    await asyncio.sleep(0.1)

    # 2. Trigger Barge-in (Press 'b')
    start_time = time.time()
    await input_provider.trigger_press("b")

    # 3. Assertions
    # We expect orchestrator to handle it.
    # Player.stop() should be called.
    # Old session cancelled.

    # Give it a moment to react
    await asyncio.sleep(0.1)

    # Check player.stop called
    mock_player.stop.assert_called()

    # Check session changed
    if pipeline.session:
        assert pipeline.session.session_id != session_id_1

    # Check old session invalidated (AC6)
    assert not pipeline.session_manager.is_valid(session_id_1)

    # AC3: Stop within <50ms.
    # We measure time from Trigger Press -> Player.stop()
    assert stop_timestamp > 0.0, "Player.stop() was not called"
    latency = stop_timestamp - start_time
    assert latency < 0.05, f"Barge-in latency too high: {latency:.4f}s"

    # Cleanup
    orch_task.cancel()
    try:
        await orch_task
    except asyncio.CancelledError:
        pass
