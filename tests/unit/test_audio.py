import pytest
from typing import Any
from unittest.mock import MagicMock, patch
import numpy as np
from app.core.audio import AudioRecorder, AudioPlayer


@pytest.mark.asyncio
@patch("app.core.audio.recorder.sd.InputStream")
async def test_audio_recorder_start_stop(mock_input_stream: MagicMock) -> None:
    """Test that AudioRecorder starts and stops recording, returning a numpy array."""
    # Setup mock stream
    mock_stream_instance: Any = mock_input_stream.return_value

    recorder = AudioRecorder(sample_rate=16000)

    # Start recording
    recorder.start()
    _ = mock_input_stream.assert_called_once()
    _ = mock_stream_instance.start.assert_called_once()

    # Simulate some audio data being recorded via callback
    call_args: Any = mock_input_stream.call_args
    assert call_args is not None
    _, kwargs = call_args
    callback: Any = kwargs.get("callback")
    assert callback is not None
    assert callable(callback)

    test_data = np.random.uniform(-1, 1, (1600, 1)).astype(np.float32)
    _ = callback(test_data, 1600, None, None)

    # Stop recording
    audio_data = recorder.stop()
    _ = mock_stream_instance.stop.assert_called_once()
    _ = mock_stream_instance.close.assert_called_once()

    assert isinstance(audio_data, np.ndarray)
    assert len(audio_data) == 1600
    assert np.allclose(audio_data, test_data.flatten())


@pytest.mark.asyncio
@patch("app.core.audio.recorder.sd.InputStream")
async def test_audio_recorder_extract_buffer(mock_input_stream: MagicMock) -> None:
    """Test that extract_buffer returns data and clears buffer."""
    recorder = AudioRecorder(sample_rate=16000)
    recorder.start()
    call_args: Any = mock_input_stream.call_args
    assert call_args is not None
    _, kwargs = call_args
    callback: Any = kwargs.get("callback")
    assert callback is not None
    assert callable(callback)

    test_data = np.random.uniform(-1, 1, (800, 1)).astype(np.float32)
    _ = callback(test_data, 800, None, None)

    # First extract
    chunk1 = recorder.extract_buffer()
    assert len(chunk1) == 800

    # Buffer should be empty now
    chunk2 = recorder.extract_buffer()
    assert len(chunk2) == 0


@pytest.mark.asyncio
@patch("app.core.audio.recorder.sd.InputStream")
async def test_audio_recorder_get_last_chunk(mock_input_stream: MagicMock) -> None:
    """Test get_last_chunk retrieves the most recent samples."""
    recorder = AudioRecorder(sample_rate=16000)
    recorder.start()
    call_args: Any = mock_input_stream.call_args
    assert call_args is not None
    _, kwargs = call_args
    callback: Any = kwargs.get("callback")
    assert callback is not None
    assert callable(callback)

    # Add 1000 samples
    data = np.arange(1000, dtype=np.float32).reshape(-1, 1)
    _ = callback(data, 1000, None, None)

    # Get last 100 samples
    chunk = recorder.get_last_chunk(100)
    assert len(chunk) == 100
    assert np.array_equal(chunk, np.arange(900, 1000, dtype=np.float32))


@pytest.mark.asyncio
@patch("app.core.audio.recorder.sd.InputStream")
async def test_audio_recorder_async_queue(mock_input_stream: MagicMock) -> None:
    """Test that AudioRecorder streams chunks via async queue."""
    recorder = AudioRecorder(sample_rate=16000)
    recorder.start()

    call_args: Any = mock_input_stream.call_args
    callback: Any = call_args[1].get("callback")

    test_data = np.ones((800, 1), dtype=np.float32)
    callback(test_data, 800, None, None)

    chunk = await recorder.get_chunk()
    assert np.array_equal(chunk, test_data)


@patch("app.core.audio.player.sd.play")
@patch("app.core.audio.player.sd.wait")
@patch("app.core.audio.player.sd.stop")
def test_audio_player_play(
    mock_stop: MagicMock, _mock_wait: MagicMock, mock_play: MagicMock
) -> None:
    """Test AudioPlayer initializes and plays data."""
    player = AudioPlayer(sample_rate=16000)

    test_data = np.zeros(1600, dtype=np.float32)
    player.play(test_data)

    _ = mock_play.assert_called_once()
    # Mocking blocking=True usually doesn't call wait() separately if play handles it, but check impl.
    # My impl uses sd.play(..., blocking=True).
    # sounddevice.play implementation: if blocking=True, it calls wait().
    # So wait() might be called.

    # Test stop
    player.stop()
    _ = mock_stop.assert_called_once()
