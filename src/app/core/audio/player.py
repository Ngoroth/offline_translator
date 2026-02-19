import threading

import numpy as np
import sounddevice as sd
from numpy.typing import NDArray

from app.core.audio.devices import resolve_device
from app.core.audio.recorder import AudioDeviceError


class AudioPlayer:
    sample_rate: int
    device_index: int | str | None
    state: str
    _lock: threading.Lock

    def __init__(self, sample_rate: int = 16000, device_index: int | str | None = None):
        self.sample_rate = sample_rate
        self.device_index = device_index
        self.state = "IDLE"
        self._lock = threading.Lock()

    def play(self, audio_data: NDArray[np.float32]) -> None:
        with self._lock:
            self.state = "PLAYING"

        try:
            with self._lock:
                if self.state != "PLAYING":
                    return

            resolved_device = resolve_device(self.device_index, is_input=False)
            sd.play(audio_data, samplerate=self.sample_rate, device=resolved_device, blocking=True)
        except Exception as e:
            error_type = type(e).__name__
            if "PortAudio" in error_type or "sounddevice" in str(type(e).__module__):
                raise AudioDeviceError(
                    message=f"Audio playback failed: {e}",
                    device=self.device_index,
                    suggestion="Check that the output device is connected and not in use by another application",
                ) from e
            raise
        finally:
            with self._lock:
                self.state = "IDLE"

    def stop(self) -> None:
        sd.stop()
        with self._lock:
            self.state = "IDLE"
