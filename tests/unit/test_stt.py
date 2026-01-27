import numpy as np
import pytest
import time
from unittest.mock import MagicMock, patch
from pydantic import ValidationError
from app.services.stt import STTService, STTModelLoadError, STTTranscriptionError
from app.core.config import STTSettings


@pytest.fixture
def stt_settings() -> STTSettings:
    return STTSettings(
        model_path="tiny", language="en", beam_size=5, device="cpu", compute_type="int8"
    )


@pytest.mark.asyncio
@patch("app.services.stt.WhisperModel")
async def test_stt_initialization(_: MagicMock, stt_settings: STTSettings) -> None:
    """Test that STTService initializes the model in a thread."""
    # We want to check if it's called. Since it might be in __init__, we might need to handle it.
    # But requirement says use asyncio.to_thread for initialization too if it's blocking.

    with patch("app.services.stt.asyncio.to_thread") as mock_to_thread:
        mock_to_thread.return_value = MagicMock()
        stt_service = STTService(stt_settings)
        assert stt_service.settings == stt_settings


@pytest.mark.asyncio
@patch("app.services.stt.WhisperModel")
async def test_stt_transcribe_async(mock_whisper: MagicMock, stt_settings: STTSettings) -> None:
    """Test that STTService transcribes audio data asynchronously."""
    mock_model_instance = mock_whisper.return_value

    mock_segment = MagicMock()
    mock_segment.text = "Hello world"

    # transcribe returns (segments_generator, info)
    mock_info = MagicMock()
    mock_info.language = "en"
    mock_info.language_probability = 0.99
    mock_model_instance.transcribe.return_value = ([mock_segment], mock_info)

    stt = STTService(stt_settings)
    audio_data = np.zeros(16000, dtype=np.float32)

    text = await stt.transcribe(audio_data)

    assert text == "Hello world"
    mock_model_instance.transcribe.assert_called_once()


@pytest.mark.asyncio
@patch("app.services.stt.WhisperModel")
async def test_stt_model_load_error(mock_whisper: MagicMock, stt_settings: STTSettings) -> None:
    """Test that STTService raises STTModelLoadError when model fails to load."""
    mock_whisper.side_effect = Exception("Model not found")

    stt_service = STTService(stt_settings)
    audio_data = np.zeros(16000, dtype=np.float32)

    with pytest.raises(STTModelLoadError):
        await stt_service.transcribe(audio_data)


@pytest.mark.asyncio
@patch("app.services.stt.WhisperModel")
async def test_stt_transcription_error(mock_whisper: MagicMock, stt_settings: STTSettings) -> None:
    """Test that STTService raises STTTranscriptionError when transcription fails."""
    mock_model_instance = mock_whisper.return_value

    # Mock transcription to raise an exception
    mock_model_instance.transcribe.side_effect = Exception("Transcription failed")

    stt_service = STTService(stt_settings)
    audio_data = np.zeros(16000, dtype=np.float32)

    with pytest.raises(STTTranscriptionError):
        await stt_service.transcribe(audio_data)


@pytest.mark.asyncio
@patch("app.services.stt.WhisperModel")
async def test_stt_performance_benchmark(
    mock_whisper: MagicMock, stt_settings: STTSettings
) -> None:
    """Test STTService meets performance requirement of < 1.0s for 5-second audio."""
    mock_model_instance = mock_whisper.return_value

    mock_segment = MagicMock()
    mock_segment.text = "Performance test transcription"

    mock_info = MagicMock()
    mock_info.language = "en"
    mock_info.language_probability = 0.95
    mock_model_instance.transcribe.return_value = ([mock_segment], mock_info)

    stt_service = STTService(stt_settings)
    # Create 5 seconds of audio at 16kHz
    audio_data = np.zeros(80000, dtype=np.float32)  # 5 * 16000 = 80000 samples

    start_time = time.time()
    text = await stt_service.transcribe(audio_data)
    end_time = time.time()

    transcription_time = end_time - start_time

    # AC 6: Performance requirement - should be < 1.0s
    assert transcription_time < 1.0, (
        f"Transcription took {transcription_time:.2f}s, expected < 1.0s"
    )
    assert text == "Performance test transcription"


@pytest.mark.asyncio
async def test_stt_settings_validation() -> None:
    """Test STTSettings validation for device and compute_type."""
    # Valid settings
    valid_settings = STTSettings(model_path="tiny", device="cpu", compute_type="int8")
    assert valid_settings.device == "cpu"
    assert valid_settings.compute_type == "int8"

    # Invalid device
    with pytest.raises(ValidationError):
        STTSettings(model_path="tiny", device="invalid_device")

    # Invalid compute_type
    with pytest.raises(ValidationError):
        STTSettings(model_path="tiny", compute_type="invalid_type")
