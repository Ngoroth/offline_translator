import asyncio
import numpy as np
from numpy.typing import NDArray
from app.core.audio import AudioRecorder, AudioPlayer


from typing import final, override


@final
class MockAudioRecorder(AudioRecorder):
    """
    Mock audio recorder for testing.
    Allows injecting predefined audio chunks.
    """

    def __init__(self, sample_rate: int = 16000):
        # Initialize parent to satisfy linter
        super().__init__(sample_rate=sample_rate)
        self.sample_rate = sample_rate
        self.buffer = []
        self._queue = asyncio.Queue()
        self.recording = False

    @override
    def start(self) -> None:
        self.buffer = []
        while not self._queue.empty():
            self._queue.get_nowait()
        self.recording = True

    @override
    def stop(self) -> NDArray[np.float32]:
        self.recording = False
        return self.extract_buffer()

    @override
    def get_last_chunk(self, num_samples: int) -> NDArray[np.float32]:
        return np.array([], dtype=np.float32)

    def inject_chunk(self, chunk: NDArray[np.float32]) -> None:
        """Simulate audio data arrival."""
        if self.recording:
            self.buffer.append(chunk)
            self._queue.put_nowait(chunk)

    @override
    async def get_chunk(self) -> NDArray[np.float32]:
        return await self._queue.get()

    @override
    def extract_buffer(self) -> NDArray[np.float32]:
        if not self.buffer:
            return np.array([], dtype=np.float32)
        data = np.concatenate(self.buffer)
        self.buffer = []
        return data.flatten()


@final
class MockAudioPlayer(AudioPlayer):
    def __init__(self, sample_rate: int = 16000):
        super().__init__(sample_rate=sample_rate)
        self.sample_rate = sample_rate
        self.played_data: list[NDArray[np.float32]] = []

    @override
    def play(self, audio_data: NDArray[np.float32]):
        self.played_data.append(audio_data)

    @override
    def stop(self):
        pass
