import numpy as np
from app.core.types import AudioPayload, TextPayload, TranslationPayload


def test_types_are_typeddicts():
    # TypedDict is a structural type, but we can verify it exists and behaves like a dict type
    assert issubclass(AudioPayload, dict)
    assert issubclass(TextPayload, dict)
    assert issubclass(TranslationPayload, dict)


def test_audio_payload_structure():
    payload: AudioPayload = {"audio": np.zeros(10), "sample_rate": 16000, "session_id": "abc"}
    assert payload["sample_rate"] == 16000
    assert payload["session_id"] == "abc"


def test_text_payload_structure():
    payload: TextPayload = {"text": "Hello", "language": "en", "session_id": "abc"}
    assert payload["text"] == "Hello"
    assert payload["session_id"] == "abc"


def test_translation_payload_structure():
    payload: TranslationPayload = {
        "text": "Hola",
        "source_lang": "en",
        "target_lang": "es",
        "session_id": "abc",
    }
    assert payload["text"] == "Hola"
    assert payload["session_id"] == "abc"


def test_payloads_have_session_id():
    from typing import get_type_hints

    assert "session_id" in get_type_hints(AudioPayload)
    assert "session_id" in get_type_hints(TextPayload)
    assert "session_id" in get_type_hints(TranslationPayload)
