import numpy as np
from app.core.types import AudioPayload, TextPayload, TranslationPayload


def test_types_are_typeddicts():
    # TypedDict is a structural type, but we can verify it exists and behaves like a dict type
    assert issubclass(AudioPayload, dict)
    assert issubclass(TextPayload, dict)
    assert issubclass(TranslationPayload, dict)


def test_audio_payload_structure():
    payload: AudioPayload = {"audio": np.zeros(10), "sample_rate": 16000}
    assert payload["sample_rate"] == 16000


def test_text_payload_structure():
    payload: TextPayload = {"text": "Hello", "language": "en"}
    assert payload["text"] == "Hello"


def test_translation_payload_structure():
    payload: TranslationPayload = {"text": "Hola", "source_lang": "en", "target_lang": "es"}
    assert payload["text"] == "Hola"
