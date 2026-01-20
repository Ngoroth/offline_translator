import numpy as np
from unittest.mock import MagicMock, patch
from app.utils.vad import VADService, SilenceDetector


@patch("app.utils.vad.webrtcvad.Vad")
def test_vad_service_is_speech(mock_webrtc_vad: MagicMock) -> None:
    mock_vad_instance = mock_webrtc_vad.return_value
    mock_vad_instance.is_speech.return_value = True

    service = VADService(sample_rate=16000)
    # 30ms frame at 16kHz is 480 samples
    audio = np.zeros(480, dtype=np.float32)

    assert service.is_speech(audio) is True
    mock_vad_instance.is_speech.assert_called_once()


def test_silence_detector_timeout() -> None:
    # 500ms threshold at 16kHz is 8000 samples
    detector = SilenceDetector(threshold_ms=500, sample_rate=16000)

    # Not silent yet (250ms)
    assert detector.is_silent_timeout(is_speech=False, num_samples=4000) is False

    # Becomes silent (total 500ms)
    assert detector.is_silent_timeout(is_speech=False, num_samples=4000) is True

    # Speech resets it
    assert detector.is_silent_timeout(is_speech=True, num_samples=480) is False
    assert detector.silence_samples == 0

    # Silent again (250ms)
    assert detector.is_silent_timeout(is_speech=False, num_samples=4000) is False


def test_silence_detector_reset() -> None:
    detector = SilenceDetector(threshold_ms=500, sample_rate=16000)
    detector.is_silent_timeout(is_speech=False, num_samples=4000)
    detector.reset()
    assert detector.silence_samples == 0
