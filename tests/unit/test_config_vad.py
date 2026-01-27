from app.core.config import (
    AppSettings,
    VADSettings,
    STTSettings,
    LLMSettings,
    TTSSettings,
    SpeakerSettings,
)
from pathlib import Path


def test_vad_settings_defaults() -> None:
    # Use a real file for tts model validation
    dummy_model = "pyproject.toml"

    settings = AppSettings(
        stt=STTSettings(model_path="foo"),
        llm=LLMSettings(model_path="foo.gguf"),
        tts=TTSSettings(model_path=dummy_model),
        speakers={"a": SpeakerSettings(from_lang="en", to_lang="es")},
    )
    assert settings.vad.threshold_ms == 500
    assert settings.vad.aggressiveness == 3


def test_vad_settings_custom() -> None:
    dummy_model = "pyproject.toml"
    vad_data = VADSettings(threshold_ms=300, aggressiveness=1)
    settings = AppSettings(
        stt=STTSettings(model_path="foo"),
        llm=LLMSettings(model_path="foo.gguf"),
        tts=TTSSettings(model_path=dummy_model),
        vad=vad_data,
        speakers={"a": SpeakerSettings(from_lang="en", to_lang="es")},
    )
    assert settings.vad.threshold_ms == 300
    assert settings.vad.aggressiveness == 1
