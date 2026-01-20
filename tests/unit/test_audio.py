import numpy as np
from unittest.mock import patch
from app.core.audio import AudioRecorder


@patch("app.core.audio.sd.InputStream")
def test_audio_recorder_start_stop(mock_input_stream):
    """Test that AudioRecorder starts and stops recording, returning a numpy array."""
    # Setup mock stream
    mock_stream_instance = mock_input_stream.return_value

    recorder = AudioRecorder(sample_rate=16000)

    # Start recording
    recorder.start()
    mock_input_stream.assert_called_once()
    mock_stream_instance.start.assert_called_once()

    # Simulate some audio data being recorded via callback
    # The callback is usually the second argument to InputStream
    callback = mock_input_stream.call_args.kwargs.get("callback")
    assert callback is not None

    test_data = np.random.uniform(-1, 1, (1600, 1)).astype(np.float32)
    callback(test_data, 1600, None, None)

    # Stop recording
    audio_data = recorder.stop()
    mock_stream_instance.stop.assert_called_once()
    mock_stream_instance.close.assert_called_once()

    assert isinstance(audio_data, np.ndarray)
    assert len(audio_data) == 1600
    assert np.allclose(audio_data, test_data.flatten())


@patch("app.core.audio.sd.InputStream")
def test_audio_recorder_extract_buffer(mock_input_stream):
    """Test that extract_buffer returns data and clears buffer."""
    recorder = AudioRecorder(sample_rate=16000)
    recorder.start()  # Need to start to have call_args
    callback = mock_input_stream.call_args.kwargs.get("callback")

    test_data = np.random.uniform(-1, 1, (800, 1)).astype(np.float32)
    callback(test_data, 800, None, None)

    # First extract
    chunk1 = recorder.extract_buffer()
    assert len(chunk1) == 800

    # Buffer should be empty now
    chunk2 = recorder.extract_buffer()
    assert len(chunk2) == 0

    # Add more data
    callback(test_data, 800, None, None)
    chunk3 = recorder.extract_buffer()
    assert len(chunk3) == 800
