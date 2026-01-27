import pytest
import asyncio
from unittest.mock import AsyncMock
from app.orchestrator.orchestrator import Orchestrator
from app.orchestrator.pipeline import TranslationPipeline
from app.core.input import BaseInput


@pytest.fixture
def mock_deps() -> dict[str, AsyncMock]:
    return {"pipeline": AsyncMock(spec=TranslationPipeline), "input": AsyncMock(spec=BaseInput)}


@pytest.fixture
def orchestrator(mock_deps: dict[str, AsyncMock]) -> Orchestrator:
    return Orchestrator(pipeline=mock_deps["pipeline"], input_provider=mock_deps["input"])


@pytest.mark.asyncio
async def test_orchestrator_loop_flow(
    orchestrator: Orchestrator, mock_deps: dict[str, AsyncMock]
) -> None:
    # Setup Input sequence: Press A -> Release A -> Cancel (to stop loop)
    # Using side_effect to simulate sequence

    mock_deps["input"].wait_for_press.side_effect = ["a", asyncio.CancelledError]
    mock_deps["input"].wait_for_release.return_value = None

    try:
        await orchestrator.run()
    except asyncio.CancelledError:
        pass

    # Verify sequence
    mock_deps["pipeline"].start_session.assert_called()
    mock_deps["input"].wait_for_release.assert_called_with("a")
    mock_deps["pipeline"].handle_input_complete.assert_called()
    mock_deps["pipeline"].wait_for_completion.assert_called()
