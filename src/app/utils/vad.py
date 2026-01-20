import webrtcvad
import numpy as np


class VADService:
    """Voice Activity Detection using WebRTC VAD."""

    vad: webrtcvad.Vad
    sample_rate: int
    frame_duration_ms: int
    frame_size: int

    def __init__(self, aggressiveness: int = 3, sample_rate: int = 16000):
        self.vad = webrtcvad.Vad(aggressiveness)
        self.sample_rate = sample_rate
        # frame_duration_ms can be 10, 20, or 30
        self.frame_duration_ms = 30
        self.frame_size = int(sample_rate * self.frame_duration_ms / 1000)

    def is_speech(self, audio_data: np.ndarray[tuple[int], np.dtype[np.float32]]) -> bool:
        """
        Returns True if the audio frame contains speech.
        Expects float32 array, converts to int16 for WebRTC VAD.
        """
        # Convert float32 [-1, 1] to int16
        int_audio = (audio_data * 32767).astype(np.int16).tobytes()

        try:
            return self.vad.is_speech(int_audio[: self.frame_size * 2], self.sample_rate)
        except Exception:
            return False


class SilenceDetector:
    """Detects sustained silence to trigger end-of-speech."""

    threshold_ms: int
    sample_rate: int
    silence_samples: int
    limit: float

    def __init__(self, threshold_ms: int = 500, sample_rate: int = 16000):
        self.threshold_ms = threshold_ms
        self.sample_rate = sample_rate
        self.silence_samples = 0
        self.limit = (threshold_ms / 1000.0) * sample_rate

    def is_silent_timeout(self, is_speech: bool, num_samples: int) -> bool:
        if is_speech:
            self.silence_samples = 0
            return False

        self.silence_samples += num_samples
        return self.silence_samples >= self.limit

    def reset(self) -> None:
        self.silence_samples = 0
