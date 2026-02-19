import webrtcvad
import numpy as np
from loguru import logger


class VADService:
    """Voice Activity Detection using WebRTC VAD."""

    vad: webrtcvad.Vad
    sample_rate: int
    frame_duration_ms: int
    frame_size: int
    _buffer: bytearray

    def __init__(self, aggressiveness: int = 3, sample_rate: int = 16000):
        self.vad = webrtcvad.Vad(aggressiveness)
        self.sample_rate = sample_rate
        # frame_duration_ms can be 10, 20, or 30
        self.frame_duration_ms = 30
        self.frame_size = int(sample_rate * self.frame_duration_ms / 1000)
        self._buffer = bytearray()

    def is_speech(self, audio_data: np.ndarray[tuple[int], np.dtype[np.float32]]) -> bool:
        """
        Returns True if the audio frame contains speech.
        Expects float32 array, converts to int16 for WebRTC VAD.
        Buffers audio internally until enough data is available for a 30ms frame.
        """
        # Convert float32 [-1, 1] to int16
        new_bytes = (audio_data * 32767).astype(np.int16).tobytes()
        self._buffer.extend(new_bytes)

        frame_bytes = self.frame_size * 2
        has_speech = False

        while len(self._buffer) >= frame_bytes:
            # We must use bytes for is_speech, so we slice and convert/cast
            # slice of bytearray is bytearray, but webrtcvad wants bytes.
            chunk = bytes(self._buffer[:frame_bytes])
            self._buffer = self._buffer[frame_bytes:]

            try:
                if self.vad.is_speech(chunk, self.sample_rate):
                    has_speech = True
            except Exception as e:
                logger.error(f"VAD is_speech error: {e}")

        return has_speech

    def reset(self) -> None:
        """Clear the internal buffer."""
        self._buffer = bytearray()


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
