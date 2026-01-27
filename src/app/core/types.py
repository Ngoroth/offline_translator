from typing import TypedDict
import numpy as np


class AudioPayload(TypedDict):
    """Payload for audio data in the pipeline."""

    audio: np.ndarray
    sample_rate: int
    session_id: str


class TextPayload(TypedDict):
    """Payload for text data (transcription) in the pipeline."""

    text: str
    language: str | None  # Language detected or specified
    session_id: str


class TranslationPayload(TypedDict):
    """Payload for translated text in the pipeline."""

    text: str
    source_lang: str
    target_lang: str
    session_id: str
