import asyncio
import numpy as np
import sounddevice as sd
from loguru import logger
from numpy.typing import NDArray


class AudioRecorder:
    sample_rate: int
    device_index: int | None
    stream: sd.InputStream | None
    buffer: list[NDArray[np.float32]]
    _queue: asyncio.Queue[NDArray[np.float32]]
    recording: bool
    _loop: asyncio.AbstractEventLoop

    def __init__(self, sample_rate: int = 16000, device_index: int | None = None):
        self.sample_rate = sample_rate
        self.device_index = device_index
        self.stream = None
        self.buffer = []
        self._queue = asyncio.Queue()
        self.recording = False
        # Recorder must be initialized within an async loop for the queue to work correctly
        self._loop = asyncio.get_running_loop()

    def start(self) -> None:
        if self.recording:
            return

        self.buffer = []
        # Clear queue for new session
        while not self._queue.empty():
            try:
                _ = self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break

        self.recording = True

        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.float32,
                device=self.device_index,
                callback=self._callback,
            )
            self.stream.start()
            logger.debug("Audio stream started")
        except Exception as e:
            logger.error(f"Failed to start audio stream: {e}")
            self.recording = False

    def stop(self) -> NDArray[np.float32]:
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        self.recording = False
        return self.extract_buffer()

    def _callback(
        self, indata: NDArray[np.float32], _frames: int, _time: object, status: object
    ) -> None:
        if status:
            logger.warning(f"Audio status: {status}")
        if self.recording:
            chunk = indata.copy()
            self.buffer.append(chunk)
            _ = self._loop.call_soon_threadsafe(self._queue.put_nowait, chunk)

    async def get_chunk(self) -> NDArray[np.float32]:
        """
        Asynchronously get the next chunk of audio data.
        """
        return await self._queue.get()

    def get_last_chunk(self, num_samples: int) -> NDArray[np.float32]:
        """
        Get the last N samples from the buffer without clearing it.
        Useful for VAD.
        """
        if not self.buffer:
            return np.array([], dtype=np.float32)

        full = np.concatenate(self.buffer)
        if len(full) < num_samples:
            return full.flatten()
        return full[-num_samples:].flatten()

    def extract_buffer(self) -> NDArray[np.float32]:
        """
        Return all recorded data and clear the buffer.
        """
        if not self.buffer:
            return np.array([], dtype=np.float32)

        data = np.concatenate(self.buffer)
        self.buffer = []
        return data.flatten()
