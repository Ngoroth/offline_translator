import asyncio
import numpy as np
import sounddevice as sd
from loguru import logger
from numpy.typing import NDArray


class AudioRecorder:
    sample_rate: int
    hardware_rate: int | None
    device_index: int | str | None
    stream: sd.InputStream | None
    buffer: list[NDArray[np.float32]]
    _queue: asyncio.Queue[NDArray[np.float32]]
    recording: bool
    _loop: asyncio.AbstractEventLoop

    def __init__(self, sample_rate: int = 16000, device_index: int | str | None = None):
        self.sample_rate = sample_rate
        # Auto-detect hardware rate logic could go here, but for now we trust config or fallback
        # If device_index is provided and we are on Pi (ALSA), likely need 48000 or 44100
        self.hardware_rate = None
        self.device_index = device_index
        self.stream = None
        self.buffer = []
        self._queue = asyncio.Queue()
        self.recording = False
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

        # Try to determine optimal sample rate if direct open fails
        rates_to_try = [self.sample_rate, 48000, 44100]

        # If user configured a specific hardware rate in future, use it.
        # For now, simplistic fallback strategy.

        for rate in rates_to_try:
            try:
                logger.debug(f"Attempting to open audio stream at {rate}Hz...")
                self.stream = sd.InputStream(
                    samplerate=rate,
                    channels=1,
                    dtype=np.float32,
                    device=self.device_index,
                    callback=self._callback,
                    blocksize=8192,  # Larger blocksize to reduce CPU load/overflows
                    latency="high",  # Relaxed latency requirements
                )
                self.stream.start()
                self.hardware_rate = rate
                logger.info(f"Audio stream started at {rate}Hz (Target: {self.sample_rate}Hz)")
                return  # Success
            except Exception as e:
                logger.warning(f"Failed to open at {rate}Hz: {e}")

        # If we get here, nothing worked
        logger.error("Failed to start audio stream. All sample rates failed.")
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
            # Resampling logic
            if self.hardware_rate and self.hardware_rate != self.sample_rate:
                # Simple decimation (only works if ratio is integer, e.g. 48000 -> 16000)
                if self.hardware_rate % self.sample_rate == 0:
                    step = int(self.hardware_rate / self.sample_rate)
                    chunk = indata[::step].copy()
                else:
                    # Non-integer ratio (e.g. 44100 -> 16000).
                    # Decimation creates artifacts here, but better than crashing.
                    # Ideally use scipy.signal.resample, but keep deps minimal for now.
                    # Using nearest-neighbor interpolation via numpy indexing
                    ratio = self.hardware_rate / self.sample_rate
                    indices = np.arange(0, len(indata), ratio).astype(int)
                    indices = indices[indices < len(indata)]  # Clip just in case
                    chunk = indata[indices].copy()
            else:
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
