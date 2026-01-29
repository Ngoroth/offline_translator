import numpy as np
from unittest.mock import MagicMock, patch
from app.utils.vad import VADService


@patch("app.utils.vad.webrtcvad.Vad")
def test_vad_buffering_small_chunks(mock_webrtc_vad: MagicMock) -> None:
    """
    Verify that VADService correctly buffers small chunks and only calls
    the underlying WebRTC VAD when a full frame (30ms) is available.
    """
    mock_vad_instance = mock_webrtc_vad.return_value
    mock_vad_instance.is_speech.return_value = True  # Assume speech for simplicity

    service = VADService(sample_rate=16000)
    # 30ms at 16kHz = 480 samples.
    # We send 3 chunks of 160 samples (10ms each).

    chunk_10ms = np.zeros(160, dtype=np.float32)

    # First chunk: Buffer has 160. Not enough.
    result1 = service.is_speech(chunk_10ms)
    assert result1 is False
    assert mock_vad_instance.is_speech.call_count == 0

    # Second chunk: Buffer has 320. Not enough.
    result2 = service.is_speech(chunk_10ms)
    assert result2 is False
    assert mock_vad_instance.is_speech.call_count == 0

    # Third chunk: Buffer has 480. Enough!
    result3 = service.is_speech(chunk_10ms)
    assert result3 is True
    assert mock_vad_instance.is_speech.call_count == 1
