import pytest
import numpy as np
from unittest.mock import MagicMock, AsyncMock
from app.orchestrator.pipeline import TranslationPipeline
from app.core.config import AppSettings
from app.orchestrator.session import SessionState


@pytest.fixture
def mock_services() -> dict[str, MagicMock | AsyncMock]:
    mock_settings = MagicMock(spec=AppSettings)
    mock_settings.speakers = {}
    return {
        "stt": AsyncMock(),
        "llm": AsyncMock(),
        "tts": AsyncMock(),
        "recorder": MagicMock(),
        "player": MagicMock(),
        "settings": mock_settings,
    }


@pytest.fixture
def pipeline(mock_services: dict[str, MagicMock | AsyncMock]) -> TranslationPipeline:
    return TranslationPipeline(
        settings=mock_services["settings"],
        stt=mock_services["stt"],
        llm=mock_services["llm"],
        tts=mock_services["tts"],
        recorder=mock_services["recorder"],
        player=mock_services["player"],
    )


@pytest.mark.asyncio
async def test_pipeline_start_stop(
    pipeline: TranslationPipeline, mock_services: dict[str, MagicMock | AsyncMock]
) -> None:
    # Start session
    session = await pipeline.start_session()

    assert pipeline.session is not None
    assert pipeline.session.state == SessionState.LISTENING
    assert len(pipeline.tasks) == 4  # stt, llm, tts, player

    mock_services["recorder"].start.assert_called_once()

    # Stop session
    await pipeline.stop_session()

    assert session.cancel_event.is_set()
    assert pipeline.session is None
    mock_services["recorder"].stop.assert_called_once()

    # Verify tasks are cancelled
    for task in pipeline.tasks:
        assert task.done() or task.cancelled()


@pytest.mark.asyncio
async def test_pipeline_graceful_completion(
    pipeline: TranslationPipeline, mock_services: dict[str, MagicMock | AsyncMock]
) -> None:
    _ = await pipeline.start_session()

    # Simulate Audio
    mock_services["recorder"].stop.return_value = np.zeros(16000, dtype=np.float32)
    mock_services["recorder"].sample_rate = 16000

    # Process
    await pipeline.handle_input_complete()

    # Verify STT Queue got item
    assert pipeline.stt_queue.qsize() > 0  # At least None or Payload+None
    # Since workers are running, they might have picked it up.

    # Wait for completion
    await pipeline.wait_for_completion()

    assert pipeline.session is None
    mock_services["recorder"].stop.assert_called()

    # Verify flow
    # STT called?
    mock_services["stt"].transcribe.assert_called()
    # LLM called? (Assuming stt returns text)
    # TTS called?
    # Player called?

    # Note: If stt.transcribe returns None/Empty by default mock, chain stops.
    # Need to config mocks to return values.


@pytest.fixture
def mock_services_with_data(
    mock_services: dict[str, MagicMock | AsyncMock],
) -> dict[str, MagicMock | AsyncMock]:
    mock_services["stt"].transcribe.return_value = "Hello"
    mock_services["llm"].translate.return_value = "Hola"

    # TTS returns async iterator
    async def async_iter(_text: str):
        # 4 bytes = 1 float32 sample
        yield b"\x00\x00\x00\x00" * 10

    # We must use MagicMock for synthesize because it returns an async generator, NOT a coroutine
    mock_services["tts"].synthesize = MagicMock(side_effect=async_iter)

    # Recorder stop returns numpy array
    mock_services["recorder"].stop.return_value = np.zeros(1600, dtype=np.float32)
    mock_services["recorder"].sample_rate = 16000
    return mock_services


@pytest.mark.asyncio
async def test_pipeline_flow(
    pipeline: TranslationPipeline, mock_services_with_data: dict[str, MagicMock | AsyncMock]
) -> None:
    # Setup pipeline with data mocks
    # Re-init pipeline with new mocks? pipeline fixture uses mock_services fixture.
    # If I mutate mock_services, pipeline sees it? Yes, same dict.

    await pipeline.start_session()
    await pipeline.handle_input_complete()
    await pipeline.wait_for_completion()

    mock_services_with_data["stt"].transcribe.assert_called()
    mock_services_with_data["llm"].translate.assert_called_with("Hello", "English", "Russian")

    # Check that synthesize was called.
    # Since we use extra_models/default voice, args might vary slightly if we didn't mock tts_model_path in session.
    # But session.tts_model_path defaults to None, so it should use default.
    # Check if synthesize was called at all.
    mock_services_with_data["tts"].synthesize.assert_called()

    mock_services_with_data["player"].play.assert_called()
