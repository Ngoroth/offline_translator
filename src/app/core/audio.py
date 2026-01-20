import numpy as np
import sounddevice as sd
from typing import Any


from app.utils.buffers import AudioRingBuffer


class AudioRecorder:
    sample_rate: int
    device_index: int | None
    _buffer: list[np.ndarray[Any, Any]]
    _stream: sd.InputStream | None
    ring_buffer: AudioRingBuffer

    def __init__(self, sample_rate: int = 16000, device_index: int | None = None):
        self.sample_rate = sample_rate
        self.device_index = device_index
        self._buffer = []
        self._stream = None
        # 10 seconds of buffer
        self.ring_buffer = AudioRingBuffer(sample_rate * 10)

    def _callback(self, indata: np.ndarray[Any, Any], frames: int, time: Any, status: Any) -> None:
        if status:
            print(f"Audio Error: {status}")
        data = indata.flatten().astype(np.float32)
        self._buffer.append(data)
        self.ring_buffer.extend(data)

    def start(self) -> None:
        self._buffer = []
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            device=self.device_index,
            channels=1,
            dtype="float32",
            callback=self._callback,
        )
        self._stream.start()

    def get_last_chunk(self, num_samples: int) -> np.ndarray[Any, Any]:
        """Get the last N samples from the ring buffer."""
        all_data = self.ring_buffer.get_all()
        if len(all_data) < num_samples:
            return all_data
        return all_data[-num_samples:]

    def extract_buffer(self) -> np.ndarray[Any, Any]:
        """Return the current buffer and clear it without stopping the stream."""
        if not self._buffer:
            return np.array([], dtype="float32")

        data = np.concatenate(self._buffer).flatten()
        self._buffer = []
        return data

    def stop(self) -> np.ndarray[Any, Any]:
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        if not self._buffer:
            return np.array([], dtype="float32")

        return np.concatenate(self._buffer).flatten()


class AudioPlayer:
    sample_rate: int
    device_index: int | None

    def __init__(self, sample_rate: int = 16000, device_index: int | None = None):
        self.sample_rate = sample_rate
        self.device_index = device_index

    def play(self, data: np.ndarray[Any, Any]) -> None:
        sd.play(data, samplerate=self.sample_rate, device=self.device_index)
        sd.wait()

    def stop(self) -> None:
        sd.stop()
