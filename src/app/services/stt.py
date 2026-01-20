import numpy as np
from faster_whisper import WhisperModel
from typing import Any


class STTService:
    def __init__(self, model_path: str, device: str = "cpu", compute_type: str = "int8"):
        """
        Initialize the Faster-Whisper model.

        Args:
            model_path: Path to the model or model size name.
            device: Device to run on ('cpu', 'cuda').
            compute_type: Quantization type ('float16', 'int8', etc.).
        """
        self.model = WhisperModel(model_path, device=device, compute_type=compute_type)

    def transcribe(self, audio_data: np.ndarray[Any, Any], language: str | None = None) -> str:
        """
        Transcribe audio data to text.

        Args:
            audio_data: Numpy array of audio samples (float32, 16kHz).
            language: Optional language code.

        Returns:
            The transcribed text.
        """
        segments, _ = self.model.transcribe(audio_data, language=language, beam_size=5)
        text = " ".join([segment.text for segment in segments]).strip()
        return text
