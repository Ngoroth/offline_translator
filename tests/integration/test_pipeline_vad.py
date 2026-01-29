import pytest
import asyncio
import numpy as np
from unittest.mock import MagicMock, AsyncMock, patch
from typing import cast
from app.orchestrator.pipeline import TranslationPipeline


@pytest.fixture
def mock_services() -> dict[str, MagicMock | AsyncMock]:
    # Use simple MagicMock instead of spec to avoid attribute issues if fields are Pydantic internal
    mock_settings = MagicMock()
    mock_settings.speakers = {}
    mock_settings.vad.aggressiveness = 3
    mock_settings.vad.threshold_ms = 500  # 500ms
    mock_settings.audio.sample_rate = 16000

    # TTS Mock that returns an async iterator (empty by default)
    async def empty_async_iter(*_args: object, **_kwargs: object):
        should_yield = False
        if should_yield:
            yield b""

    tts_mock = MagicMock()
    tts_mock.synthesize.side_effect = empty_async_iter

    return {
        "stt": AsyncMock(),
        "llm": AsyncMock(),
        "tts": tts_mock,
        "recorder": MagicMock(),
        "player": MagicMock(),
        "settings": mock_settings,
    }


@pytest.fixture
def pipeline(mock_services: dict[str, MagicMock | AsyncMock]) -> TranslationPipeline:
    # We mock VADService inside the test or fixture
    with patch("app.orchestrator.pipeline.VADService") as MockVAD:
        # Instance mock
        mock_vad_instance = MockVAD.return_value
        # Default behavior
        mock_vad_instance.is_speech.return_value = False

        return TranslationPipeline(
            settings=mock_services["settings"],
            stt=mock_services["stt"],
            llm=mock_services["llm"],
            tts=mock_services["tts"],
            recorder=mock_services["recorder"],
            player=mock_services["player"],
        )


@pytest.mark.asyncio
async def test_vad_harvesting_flow(
    pipeline: TranslationPipeline, mock_services: dict[str, MagicMock | AsyncMock]
) -> None:
    # Setup VAD to simulate speech then silence
    # Threshold is 500ms.
    # We will send 10 chunks of 100ms.
    # Chunks 1-5: Speech
    # Chunks 6-10: Silence -> Trigger harvest at chunk 10 (Total 500ms silence)

    # 100ms at 16kHz = 1600 samples
    chunk_size = 1600

    # Create chunks
    speech_chunk = np.ones(chunk_size, dtype=np.float32) * 0.5
    silence_chunk = np.zeros(chunk_size, dtype=np.float32)

    # Recorder get_chunk simulation
    chunk_queue: asyncio.Queue[np.ndarray] = asyncio.Queue()
    for _ in range(5):
        await chunk_queue.put(speech_chunk)
    for _ in range(6):  # 6 chunks of silence to ensure crossing threshold
        await chunk_queue.put(silence_chunk)

    # Mock recorder.get_chunk to pop from our queue
    mock_services["recorder"].get_chunk.side_effect = lambda: chunk_queue.get()
    mock_services["recorder"].sample_rate = 16000

    # Mock extract_buffer to return "recorded audio"
    mock_services["recorder"].extract_buffer.return_value = np.concatenate(
        [speech_chunk] * 5 + [silence_chunk] * 5
    )

    # Setup VAD Service Mock logic
    # pipeline.vad_service is the instance.
    # We need to make it return True for speech chunks, False for silence
    def vad_side_effect(chunk: np.ndarray) -> bool:
        # Simple heuristic: if chunk has energy, it's speech
        return float(np.max(np.abs(chunk))) > 0.1

    cast(MagicMock, pipeline.vad_service.is_speech).side_effect = vad_side_effect

    # Start Session
    await pipeline.start_session()

    # Wait for VAD worker to process queue
    # 11 chunks * processing time
    try:
        await asyncio.wait_for(chunk_queue.join(), timeout=2.0)
    except asyncio.TimeoutError:
        pass  # Queue might not be marked done, but empty is enough

    # Give a little extra time for the harvest logic after queue empty
    await asyncio.sleep(0.1)

    # Verify STT Worker processed the item
    # Since start_session starts stt_worker, it consumes the queue.
    # So we check if transcribe was called.
    mock_services["stt"].transcribe.assert_called()

    # We can also check args
    args, _ = mock_services["stt"].transcribe.call_args
    audio_arg = args[0]
    assert len(audio_arg) > 0

    # Stop Session
    await pipeline.stop_session()


@pytest.mark.asyncio
async def test_vad_multiple_segments_harvested(
    mock_services: dict[str, MagicMock | AsyncMock],
) -> None:
    """
    Test FR11: Users can speak up to 10 phrases in one hold session.

    Scenario:
    - User presses PTT
    - Speaks phrase 1
    - Pauses (silence triggers harvest)
    - Speaks phrase 2
    - Pauses (silence triggers harvest again)
    - Releases PTT

    Expected: Both phrases should be sent to STT (2 calls to transcribe).

    This test was added during Epic 3 retrospective after discovering
    that state transitions were blocking multi-segment harvesting.
    """
    with patch("app.orchestrator.pipeline.VADService") as MockVAD:
        mock_vad_instance = MockVAD.return_value
        mock_vad_instance.is_speech.return_value = False  # Default

        pipeline = TranslationPipeline(
            settings=mock_services["settings"],
            stt=mock_services["stt"],
            llm=mock_services["llm"],
            tts=mock_services["tts"],
            recorder=mock_services["recorder"],
            player=mock_services["player"],
        )

        # 100ms at 16kHz = 1600 samples
        chunk_size = 1600
        speech_chunk = np.ones(chunk_size, dtype=np.float32) * 0.5
        silence_chunk = np.zeros(chunk_size, dtype=np.float32)

        # Sequence: speech(5) -> silence(6) -> speech(5) -> silence(6)
        # This simulates two phrases with pauses between them
        chunk_queue: asyncio.Queue[np.ndarray] = asyncio.Queue()

        # First phrase (500ms speech)
        for _ in range(5):
            await chunk_queue.put(speech_chunk)
        # First pause (600ms silence -> triggers harvest at 500ms threshold)
        for _ in range(6):
            await chunk_queue.put(silence_chunk)

        # Second phrase (500ms speech)
        for _ in range(5):
            await chunk_queue.put(speech_chunk)
        # Second pause (600ms silence -> triggers second harvest)
        for _ in range(6):
            await chunk_queue.put(silence_chunk)

        # Track extract_buffer calls - return different audio each time
        segment_1 = np.concatenate([speech_chunk] * 5)
        segment_2 = np.concatenate([speech_chunk] * 5 + [silence_chunk] * 1)
        extract_call_count = 0

        def extract_buffer_side_effect() -> np.ndarray:
            nonlocal extract_call_count
            extract_call_count += 1
            if extract_call_count == 1:
                return segment_1
            return segment_2

        mock_services["recorder"].get_chunk.side_effect = lambda: chunk_queue.get()
        mock_services["recorder"].sample_rate = 16000
        mock_services["recorder"].extract_buffer.side_effect = extract_buffer_side_effect

        # VAD logic: energy-based detection
        def vad_side_effect(chunk: np.ndarray) -> bool:
            return float(np.max(np.abs(chunk))) > 0.1

        pipeline.vad_service.is_speech = MagicMock(side_effect=vad_side_effect)

        # Start Session
        await pipeline.start_session()

        # Wait for VAD to process all chunks
        try:
            await asyncio.wait_for(chunk_queue.join(), timeout=3.0)
        except asyncio.TimeoutError:
            pass

        # Give extra time for harvest and processing
        await asyncio.sleep(0.3)

        # CRITICAL ASSERTION: STT should be called TWICE (once per segment)
        # This was the bug - before the fix, only 1 call would happen
        call_count = mock_services["stt"].transcribe.call_count
        assert call_count >= 2, (
            f"Expected at least 2 STT calls for 2 phrases, got {call_count}. "
            "This indicates multi-segment harvesting is broken (FR11 violation)."
        )

        # Cleanup
        await pipeline.stop_session()
