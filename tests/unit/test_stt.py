import numpy as np
from unittest.mock import MagicMock, patch
from app.services.stt import STTService


@patch("app.services.stt.WhisperModel")
def test_stt_transcribe(mock_whisper):
    """Test that STTService transcribes audio data."""
    # Setup mock model
    mock_model_instance = mock_whisper.return_value
    # mock_model_instance.transcribe returns (segments, info)
    mock_segment = MagicMock()
    mock_segment.text = "Hello world"
    mock_model_instance.transcribe.return_value = ([mock_segment], MagicMock())

    stt = STTService(model_path="models/stt/test")

    audio_data = np.zeros(16000, dtype=np.float32)
    text = stt.transcribe(audio_data)

    assert text == "Hello world"
    mock_model_instance.transcribe.assert_called_once()
