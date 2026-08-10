import pytest
from typing import Any
from unittest.mock import MagicMock, patch
import numpy as np
from app.core.audio import AudioRecorder, AudioPlayer
from app.core.audio.recorder import AudioDeviceError
from app.core.audio.recorder_sounddevice import SoundDeviceAudioRecorder


@pytest.mark.asyncio
@patch("app.core.audio.recorder.subprocess.Popen")
async def test_audio_recorder_start_stop(mock_popen: MagicMock) -> None:
    """Test that AudioRecorder starts and stops recording, returning a numpy array."""
    # Setup mock process
    mock_process: Any = mock_popen.return_value
    mock_process.poll.return_value = None
    mock_process.stdout = MagicMock()
    mock_process.stderr = MagicMock()

    # Simulate audio data from arecord (S16_LE bytes)
    test_samples = np.random.randint(-32768, 32767, 1600, dtype=np.int16)
    test_bytes = test_samples.tobytes()
    mock_process.stdout.read.return_value = test_bytes

    recorder = AudioRecorder(sample_rate=16000)

    # Start recording
    recorder.start()
    _ = mock_popen.assert_called_once()

    # Wait for the read thread to process
    import time

    time.sleep(0.1)

    # Stop recording
    audio_data = recorder.stop()
    _ = mock_process.terminate.assert_called_once()

    assert isinstance(audio_data, np.ndarray)
    assert audio_data.dtype == np.float32


@pytest.mark.asyncio
@patch("app.core.audio.recorder.subprocess.Popen")
async def test_audio_recorder_extract_buffer(mock_popen: MagicMock) -> None:
    """Test that extract_buffer returns data and clears buffer."""
    mock_process: Any = mock_popen.return_value
    mock_process.poll.return_value = None
    mock_process.stdout = MagicMock()
    mock_process.stderr = MagicMock()

    # Simulate audio data (S16_LE bytes) - return once then stop
    test_samples = np.random.randint(-32768, 32767, 800, dtype=np.int16)
    test_bytes = test_samples.tobytes()

    call_count = 0

    def mock_read(_size: int) -> bytes:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return test_bytes
        # Simulate process termination after first read
        mock_process.poll.return_value = 0
        return b""

    mock_process.stdout.read = mock_read

    recorder = AudioRecorder(sample_rate=16000)
    recorder.start()

    import time

    time.sleep(0.15)

    # Stop recording
    recorder.recording = False
    time.sleep(0.05)

    # First extract
    chunk1 = recorder.extract_buffer()
    assert len(chunk1) == 800

    # Buffer should be empty now
    chunk2 = recorder.extract_buffer()
    assert len(chunk2) == 0


@pytest.mark.asyncio
@patch("app.core.audio.recorder.subprocess.Popen")
async def test_audio_recorder_async_queue(mock_popen: MagicMock) -> None:
    """Test that AudioRecorder streams chunks via async queue."""
    mock_process: Any = mock_popen.return_value
    mock_process.poll.return_value = None
    mock_process.stdout = MagicMock()
    mock_process.stderr = MagicMock()

    # Simulate audio data (S16_LE bytes)
    test_samples = np.ones(800, dtype=np.int16)
    test_bytes = test_samples.tobytes()
    mock_process.stdout.read.return_value = test_bytes

    recorder = AudioRecorder(sample_rate=16000)
    recorder.start()

    import time

    time.sleep(0.1)

    chunk = await recorder.get_chunk()
    assert len(chunk) == 800


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


class TestAudioDeviceError:
    def test_audio_device_error_raised_on_arecord_not_found(self) -> None:
        with patch("app.core.audio.recorder.subprocess.Popen") as mock_popen:
            mock_popen.side_effect = FileNotFoundError("arecord not found")

            recorder = AudioRecorder(sample_rate=16000)

            with pytest.raises(AudioDeviceError) as exc_info:
                recorder.start()

            assert "arecord command not found" in str(exc_info.value)
            assert (
                exc_info.value.suggestion
                == "Install alsa-utils: 'sudo apt install alsa-utils' (Linux/RPi) or use Windows audio backend"
            )

    def test_audio_device_error_raised_on_process_exit(self) -> None:
        with patch("app.core.audio.recorder.subprocess.Popen") as mock_popen:
            mock_process: Any = MagicMock()
            mock_process.poll.return_value = 1
            mock_process.stderr = MagicMock()
            mock_process.stderr.read.return_value = b"error: device not found"
            mock_popen.return_value = mock_process

            recorder = AudioRecorder(sample_rate=16000, device_index="test_device")

            with pytest.raises(AudioDeviceError) as exc_info:
                recorder.start()

            assert "arecord process exited immediately" in str(exc_info.value)

    def test_audio_device_error_attributes(self) -> None:
        error = AudioDeviceError(
            message="Test error",
            device="test_device",
            suggestion="Test suggestion",
        )

        assert error.message == "Test error"
        assert error.device == "test_device"
        assert error.suggestion == "Test suggestion"
        assert "Test error" in str(error)
        assert "test_device" in str(error)


@patch("app.core.audio.recorder_sounddevice.sd.InputStream")
def test_sounddevice_recorder_wraps_startup_errors(mock_input_stream: MagicMock) -> None:
    mock_input_stream.side_effect = RuntimeError("PortAudioError: invalid device")

    recorder = SoundDeviceAudioRecorder(sample_rate=16000, device_index=7)

    with pytest.raises(AudioDeviceError) as exc_info:
        recorder.start()

    assert "Failed to start sounddevice input stream" in str(exc_info.value)
    assert "microphone permissions" in exc_info.value.suggestion
