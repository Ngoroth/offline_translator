import threading
import numpy as np
import sounddevice as sd
from numpy.typing import NDArray


class AudioPlayer:
    sample_rate: int
    device_index: int | None
    state: str
    _lock: threading.Lock

    def __init__(self, sample_rate: int = 16000, device_index: int | None = None):
        self.sample_rate = sample_rate
        self.device_index = device_index
        self.state = "IDLE"
        self._lock = threading.Lock()

    def play(self, audio_data: NDArray[np.float32]):
        """
        Play audio data blocking.
        """
        with self._lock:
            self.state = "PLAYING"

        try:
            # Race condition check: If stop() was called right after we set PLAYING
            # but before we call sd.play, state might be IDLE.
            with self._lock:
                if self.state != "PLAYING":
                    return

            sd.play(
                audio_data, samplerate=self.sample_rate, device=self.device_index, blocking=True
            )
        finally:
            with self._lock:
                self.state = "IDLE"

    def stop(self):
        """
        Immediately stops the output stream, clears buffer, and resets state.
        Thread-safe.
        """
        sd.stop()
        with self._lock:
            self.state = "IDLE"
