import numpy as np
from unittest.mock import MagicMock, patch
from app.services.tts import TTSService


@patch("app.services.tts.PiperVoice.load")
def test_tts_synthesize(mock_load: MagicMock) -> None:
    """Test that TTSService synthesizes text to audio."""
    # Setup mock voice
    mock_voice = MagicMock()
    _ = mock_load.return_value = mock_voice

    # Mock synthesize to yield one chunk of silence
    mock_chunk = MagicMock()
    mock_chunk.audio_int16_array = np.zeros(16000, dtype=np.int16)
    mock_voice.synthesize.return_value = [mock_chunk]

    tts = TTSService(model_path="models/tts/test.onnx")

    audio = tts.synthesize("Hello")
    assert isinstance(audio, np.ndarray)
    assert len(audio) == 16000
    _ = mock_voice.synthesize.assert_called_once()
