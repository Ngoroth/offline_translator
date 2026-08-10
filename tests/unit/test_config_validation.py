import pytest
from pydantic import ValidationError
from app.core.config import (
    AppSettings,
    STTSettings,
    LLMSettings,
    TTSSettings,
    SpeakerSettings,
)


def test_config_validation_valid(tmp_path):
    """Test that valid configuration passes validation."""
    # Create dummy model files
    (tmp_path / "stt.bin").touch()
    (tmp_path / "llm.gguf").touch()

    settings = AppSettings(
        stt=STTSettings(model_path=str(tmp_path / "stt.bin")),
        llm=LLMSettings(model_path=str(tmp_path / "llm.gguf")),
        tts=TTSSettings(model_path=str(tmp_path / "voice_a.onnx")),
        speakers={
            "a": SpeakerSettings(key="space", from_lang="en", to_lang="ru"),
            "b": SpeakerSettings(key="alt", from_lang="ru", to_lang="en"),
        },
    )
    assert settings.stt.model_path == str(tmp_path / "stt.bin")


def test_config_validation_missing_llm(tmp_path):
    """Test that AppSettings accepts missing model files.

    File existence validation is now handled by StartupVerifier,
    not by AppSettings. This allows config loading to succeed even
    when models haven't been downloaded yet.
    """
    (tmp_path / "stt.bin").touch()

    # Should NOT raise ValidationError - validation deferred to StartupVerifier
    settings = AppSettings(
        stt=STTSettings(model_path=str(tmp_path / "stt.bin")),
        llm=LLMSettings(model_path=str(tmp_path / "missing.gguf")),
        tts=TTSSettings(model_path=str(tmp_path / "voice.onnx")),
    )
    assert settings.llm.model_path == str(tmp_path / "missing.gguf")


def test_config_validation_duplicate_keys(tmp_path):
    """Test validation fails if speaker keys are identical."""
    (tmp_path / "stt.bin").touch()
    (tmp_path / "llm.gguf").touch()

    with pytest.raises(ValidationError) as excinfo:
        AppSettings(
            stt=STTSettings(model_path=str(tmp_path / "stt.bin")),
            llm=LLMSettings(model_path=str(tmp_path / "llm.gguf")),
            tts=TTSSettings(model_path=str(tmp_path / "voice.onnx")),
            speakers={
                "a": SpeakerSettings(key="space", from_lang="en", to_lang="ru"),
                "b": SpeakerSettings(key="space", from_lang="ru", to_lang="en"),  # Duplicate
            },
        )
    assert "Speaker keys must be distinct" in str(excinfo.value)
