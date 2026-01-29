import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from app.orchestrator.orchestrator import Orchestrator
from app.orchestrator.pipeline import TranslationPipeline
from app.core.input import BaseInput


@pytest.fixture
def mock_pipeline() -> MagicMock:
    p = MagicMock(spec=TranslationPipeline)
    p.start_session = AsyncMock()
    p.handle_input_complete = AsyncMock()
    p.wait_for_completion = AsyncMock()
    p.stop_session = AsyncMock()
    p.handle_barge_in = AsyncMock()
    # Mock session property
    p.session = None
    return p


@pytest.fixture
def mock_input() -> MagicMock:
    i = MagicMock(spec=BaseInput)
    i.wait_for_press = AsyncMock()
    i.wait_for_release = AsyncMock()
    return i


@pytest.mark.asyncio
async def test_orchestrator_barge_in(mock_pipeline: MagicMock, mock_input: MagicMock) -> None:
    """
    Test that Orchestrator handles PTT press during processing (Barge-in).
    """
    orchestrator = Orchestrator(pipeline=mock_pipeline, input_provider=mock_input)

    # Scenario:
    # 1. First PTT Press -> Start Session 1
    # 2. Pipeline starts processing/playing (wait_for_completion called)
    # 3. Second PTT Press (Barge-in) happens BEFORE completion finishes
    # 4. Pipeline.handle_barge_in() should be called
    # 5. Session 2 starts

    # Setup mocks
    mock_input.wait_for_press.side_effect = [
        "a",
        "b",
        asyncio.CancelledError,
    ]  # Press 1, Press 2, Stop
    mock_input.wait_for_release.side_effect = [None, None]

    # When start_session is called, set session to active
    async def start_session_side_effect(_role: str = "a"):
        mock_pipeline.session = MagicMock()
        return mock_pipeline.session

    mock_pipeline.start_session.side_effect = start_session_side_effect

    # Run
    try:
        await orchestrator.run()
    except asyncio.CancelledError:
        pass

    # Verification
    # We expect 2 start_session calls
    assert mock_pipeline.start_session.call_count == 2

    # We expect handle_barge_in called ONCE (for the barge-in)
    # The current implementation will NOT call it.
    mock_pipeline.handle_barge_in.assert_called()
