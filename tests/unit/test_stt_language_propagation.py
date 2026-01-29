import pytest
import numpy as np
from unittest.mock import MagicMock, AsyncMock
from app.services.stt import STTService


@pytest.mark.asyncio
async def test_stt_transcribe_language_param():
    """
    Verify that STTService.transcribe accepts a language parameter
    and uses it for transcription (mocking the internal model).
    """
    settings = MagicMock()
    settings.language = "default_en"
    settings.beam_size = 5
    settings.device = "cpu"
    settings.compute_type = "int8"
    settings.model_path = "mock_model"

    service = STTService(settings)

    # Mock internal _get_model and model.transcribe
    service._get_model = AsyncMock()
    mock_model = MagicMock()
    service._get_model.return_value = mock_model

    # Mock transcribe return
    # transcribe returns (segments, info)
    mock_segment = MagicMock()
    mock_segment.text = "Hello"

    # Mock info object with format-friendly values
    mock_info = MagicMock()
    mock_info.language = "ru"
    mock_info.language_probability = 0.99

    mock_model.transcribe.return_value = ([mock_segment], mock_info)

    # Act
    audio = np.zeros(16000, dtype=np.float32)
    await service.transcribe(audio, language="ru")

    # Assert
    # Verify model.transcribe was called with language="ru"
    _, kwargs = mock_model.transcribe.call_args
    assert kwargs["language"] == "ru"

    # Act - Default
    await service.transcribe(audio)

    # Assert
    _, kwargs = mock_model.transcribe.call_args
    assert kwargs["language"] == "default_en"
