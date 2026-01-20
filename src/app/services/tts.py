from collections.abc import Iterator
import numpy as np
from piper.voice import PiperVoice
from pathlib import Path


class TTSService:
    voice: PiperVoice

    def __init__(self, model_path: str, config_path: str | None = None):
        """
        Initialize the Piper TTS model.
        """
        p_model = Path(model_path)
        p_config = (
            Path(config_path) if config_path else p_model.with_suffix(p_model.suffix + ".json")
        )

        if not p_config.exists():
            # Piper models usually have a .json file with the same name as .onnx
            p_config = p_model.parent / (p_model.stem + ".onnx.json")

        self.voice = PiperVoice.load(
            str(p_model), config_path=str(p_config) if p_config.exists() else None
        )

    def synthesize_stream(
        self, text: str
    ) -> Iterator[np.ndarray[tuple[int], np.dtype[np.float32]]]:
        """
        Synthesize text to audio data (float32) and yield chunks.
        """
        for chunk in self.voice.synthesize(text):
            yield chunk.audio_int16_array.astype(np.float32) / 32768.0

    def synthesize(self, text: str) -> np.ndarray[tuple[int], np.dtype[np.float32]]:
        """
        Synthesize text to audio data (float32).
        """
        # Piper outputs 16-bit PCM at its native sample rate (usually 22050 or 16000)
        # We need to collect all chunks and convert to float32
        audio_chunks: list[np.ndarray[tuple[int], np.dtype[np.float32]]] = []

        for chunk in self.voice.synthesize(text):
            # chunk has audio_int16_array (numpy array)
            # Convert to float32
            audio_chunks.append(chunk.audio_int16_array.astype(np.float32) / 32768.0)

        if not audio_chunks:
            return np.array([], dtype=np.float32)

        return np.concatenate(audio_chunks)

    def _synthesize_to_array(self, text: str) -> np.ndarray[tuple[int], np.dtype[np.float32]]:
        """Internal helper for testing/mocking."""
        return self.synthesize(text)
