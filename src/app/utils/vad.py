import webrtcvad
import numpy as np


class VADService:
    """Voice Activity Detection using WebRTC VAD."""

    def __init__(self, aggressiveness: int = 3, sample_rate: int = 16000):
        self.vad = webrtcvad.Vad(aggressiveness)
        self.sample_rate = sample_rate
        # webrtcvad requires 10, 20, or 30ms frames
        self.frame_duration_ms = 30
        self.frame_size = int(sample_rate * self.frame_duration_ms / 1000)

    def is_speech(self, audio_data: np.ndarray) -> bool:
        """
        Check if the audio chunk contains speech.
        Expects float32 array in range [-1, 1].
        """
        # Convert float32 to int16 for webrtcvad
        int_audio = (audio_data * 32767).astype(np.int16).tobytes()

        # WebRTC VAD requires specific frame lengths
        # If the input is not exactly the frame size, we check the first frame
        if len(audio_data) < self.frame_size:
            return False

        try:
            return self.vad.is_speech(int_audio[: self.frame_size * 2], self.sample_rate)
        except Exception:
            return False


class SilenceDetector:
    """Detects sustained silence to trigger end-of-speech."""

    def __init__(self, threshold_ms: int = 500, sample_rate: int = 16000):
        self.threshold_ms = threshold_ms
        self.sample_rate = sample_rate
        self.silence_samples = 0
        self.limit = (threshold_ms / 1000) * sample_rate

    def is_silent_timeout(self, is_speech: bool, num_samples: int) -> bool:
        if is_speech:
            self.silence_samples = 0
            return False
        else:
            self.silence_samples += num_samples
            return self.silence_samples >= self.limit

    def reset(self):
        self.silence_samples = 0
