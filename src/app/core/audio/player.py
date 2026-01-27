import numpy as np
import sounddevice as sd
from numpy.typing import NDArray


class AudioPlayer:
    sample_rate: int
    device_index: int | None

    def __init__(self, sample_rate: int = 16000, device_index: int | None = None):
        self.sample_rate = sample_rate
        self.device_index = device_index

    def play(self, audio_data: NDArray[np.float32]):
        """
        Play audio data blocking.
        """
        sd.play(audio_data, samplerate=self.sample_rate, device=self.device_index, blocking=True)

    def stop(self):
        sd.stop()
