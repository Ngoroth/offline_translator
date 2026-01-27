import numpy as np
from unittest.mock import MagicMock, patch
from app.utils.vad import VADService


@patch("app.utils.vad.webrtcvad.Vad")
def test_vad_service_process_multiframe_chunk(mock_webrtc_vad: MagicMock) -> None:
    mock_vad_instance = mock_webrtc_vad.return_value

    # Setup VAD to return False for first frame, True for second
    # We expect is_speech to iterate over frames
    mock_vad_instance.is_speech.side_effect = [False, True]

    service = VADService(sample_rate=16000)
    # 60ms frame at 16kHz is 960 samples (2 * 480)
    # First half (30ms) will be "silence", second half "speech"
    audio = np.zeros(960, dtype=np.float32)

    # This should return True if it processes the second frame
    assert service.is_speech(audio) is True

    # Should have been called twice
    assert mock_vad_instance.is_speech.call_count == 2
