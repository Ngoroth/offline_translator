import pytest
import numpy as np
from unittest.mock import MagicMock, patch, ANY
from app.services.tts import TTSService
from app.core.config import TTSSettings


# Mock PiperVoice
@pytest.fixture
def mock_piper_setup():
    with patch("app.services.tts.PiperVoice") as mock_class:
        voice_instance = MagicMock()
        mock_class.load.return_value = voice_instance
        # Default sample rate to avoid mock math issues
        voice_instance.config.sample_rate = 16000
        yield mock_class, voice_instance


@pytest.fixture
def tts_settings():
    return TTSSettings(model_path=__file__, sample_rate=16000)


@pytest.mark.asyncio
async def test_tts_initialization(
    mock_piper_setup: tuple[MagicMock, MagicMock], tts_settings: TTSSettings
) -> None:
    mock_class, _ = mock_piper_setup

    with patch("pathlib.Path.is_file", return_value=True):
        service = TTSService(tts_settings)
        # Check default_voice instead of voice
        assert service.default_voice is not None
        mock_class.load.assert_called_once()


@pytest.mark.asyncio
async def test_synthesize_conversion_int16_to_float32(
    mock_piper_setup: tuple[MagicMock, MagicMock], tts_settings: TTSSettings
) -> None:
    _, mock_instance = mock_piper_setup

    # Configure mock instance BEFORE init
    mock_instance.config.sample_rate = 16000

    with patch("pathlib.Path.is_file", return_value=True):
        service = TTSService(tts_settings)

    # Piper yields int16 bytes
    fake_int16_data = np.array([0, 32767, -32768, 0], dtype=np.int16).tobytes()

    # Mock Chunk object
    mock_chunk = MagicMock()
    mock_chunk.audio_int16_bytes = fake_int16_data

    # synthesize returns iterator of Chunks
    mock_instance.synthesize.return_value = iter([mock_chunk])

    chunks = []
    async for chunk in service.synthesize("test text", speaker_id=5):
        chunks.append(chunk)

    # Verify speaker_id was passed
    mock_instance.synthesize.assert_called()
    args, _ = mock_instance.synthesize.call_args
    assert args[0] == "test text"

    assert len(chunks) == 1
    float_data = np.frombuffer(chunks[0], dtype=np.float32)
    assert len(float_data) == 4
    assert np.allclose(float_data, [0.0, 0.99996948, -1.0, 0.0], atol=1e-4)


@pytest.mark.asyncio
async def test_synthesize_resampling(
    mock_piper_setup: tuple[MagicMock, MagicMock], tts_settings: TTSSettings
) -> None:
    """Test resampling from 22050Hz to 16000Hz"""
    _, mock_instance = mock_piper_setup

    # Configure mock instance BEFORE init
    mock_instance.config.sample_rate = 22050

    with patch("pathlib.Path.is_file", return_value=True):
        service = TTSService(tts_settings)

    # 22050 Hz input
    t = np.linspace(0, 1.0, 22050, endpoint=False)
    sine_wave = (np.sin(2 * np.pi * 440 * t) * 32000).astype(np.int16)

    chunk1 = sine_wave[:11025].tobytes()
    chunk2 = sine_wave[11025:].tobytes()

    mock_chunk1 = MagicMock()
    mock_chunk1.audio_int16_bytes = chunk1
    mock_chunk2 = MagicMock()
    mock_chunk2.audio_int16_bytes = chunk2

    mock_instance.synthesize.return_value = iter([mock_chunk1, mock_chunk2])

    full_output = b""
    async for chunk in service.synthesize("test"):
        full_output += chunk

    output_floats = np.frombuffer(full_output, dtype=np.float32)

    # Assertions
    # With resampling, we expect roughly 16000 samples (+/- small error due to buffering/chunking)
    assert 15900 < len(output_floats) < 16100
    assert np.max(np.abs(output_floats)) > 0.5


@pytest.mark.asyncio
async def test_synthesize_cancelled(
    mock_piper_setup: tuple[MagicMock, MagicMock], tts_settings: TTSSettings
) -> None:
    _, mock_instance = mock_piper_setup
    mock_session_manager = MagicMock()
    mock_session_manager.is_valid.return_value = False

    with patch("pathlib.Path.is_file", return_value=True):
        service = TTSService(tts_settings, session_manager=mock_session_manager)

    chunks = []
    async for chunk in service.synthesize("test", session_id="abc"):
        chunks.append(chunk)

    assert len(chunks) == 0
    mock_instance.synthesize.assert_not_called()
