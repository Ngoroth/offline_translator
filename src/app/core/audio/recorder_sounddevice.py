import asyncio

import numpy as np
import sounddevice as sd
from loguru import logger
from numpy.typing import NDArray

from app.core.audio.recorder import AudioDeviceError


class SoundDeviceAudioRecorder:
    sample_rate: int
    device_index: int | str | None
    stream: sd.InputStream | None
    buffer: list[NDArray[np.float32]]
    _queue: asyncio.Queue[NDArray[np.float32]]
    recording: bool
    _loop: asyncio.AbstractEventLoop

    def __init__(self, sample_rate: int = 16000, device_index: int | str | None = None):
        self.sample_rate = sample_rate
        self.device_index = device_index
        self.stream = None
        self.buffer = []
        self._queue = asyncio.Queue()
        self.recording = False
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = asyncio.get_event_loop()

    def start(self) -> None:
        if self.recording:
            return

        self.buffer = []
        while not self._queue.empty():
            try:
                _ = self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break

        def callback(
            indata: NDArray[np.float32],
            _frames: int,
            _time: sd.CallbackFlags,
            status: sd.CallbackFlags,
        ) -> None:
            if status:
                logger.warning(f"sounddevice input stream status: {status}")

            chunk = np.copy(indata[:, 0]).astype(np.float32)
            self.buffer.append(chunk)
            if self.recording:
                _ = self._loop.call_soon_threadsafe(self._queue.put_nowait, chunk)

        self.recording = True
        device = self.device_index

        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                device=device,
                channels=1,
                dtype="float32",
                callback=callback,
            )
            self.stream.start()
        except Exception as exc:
            self.recording = False
            self.stream = None
            error_type = type(exc).__name__
            if "PortAudio" in error_type or "sounddevice" in str(type(exc).__module__):
                raise AudioDeviceError(
                    message=f"Failed to start sounddevice input stream: {exc}",
                    device=device,
                    suggestion="Check microphone permissions and that the selected input device is available",
                ) from exc
            raise AudioDeviceError(
                message=f"Failed to start recorder stream: {exc}",
                device=device,
                suggestion="Verify the input device configuration for the selected profile",
            ) from exc

    def stop(self) -> NDArray[np.float32]:
        self.recording = False
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        return self.extract_buffer()

    async def get_chunk(self) -> NDArray[np.float32]:
        return await self._queue.get()

    def get_last_chunk(self, num_samples: int) -> NDArray[np.float32]:
        if not self.buffer:
            return np.array([], dtype=np.float32)
        full = np.concatenate(self.buffer)
        if len(full) < num_samples:
            return full.flatten()
        return full[-num_samples:].flatten()

    def extract_buffer(self) -> NDArray[np.float32]:
        if not self.buffer:
            return np.array([], dtype=np.float32)
        data = np.concatenate(self.buffer)
        self.buffer = []
        return data.flatten()
