import pytest
from pydantic import ValidationError
from app.core.config import AppSettings, STTSettings, LLMSettings, TTSSettings


def test_config_validation_valid(tmp_path):
    """Test that valid configuration passes validation."""
    # Create dummy model files
    (tmp_path / "stt.bin").touch()
    (tmp_path / "llm.gguf").touch()
    (tmp_path / "voice_a.onnx").touch()
    (tmp_path / "voice_b.onnx").touch()

    settings = AppSettings(
        stt=STTSettings(model_path=str(tmp_path / "stt.bin")),
        llm=LLMSettings(model_path=str(tmp_path / "llm.gguf")),
        tts=TTSSettings(model_path=str(tmp_path / "voice_a.onnx")),
        speaker_a_voice=str(tmp_path / "voice_a.onnx"),
        speaker_b_voice=str(tmp_path / "voice_b.onnx"),
        speaker_a_key="space",
        speaker_b_key="alt",
    )
    assert settings.stt.model_path == str(tmp_path / "stt.bin")


def test_config_validation_missing_llm(tmp_path):
    """Test that AppSettings accepts missing model files.

    File existence validation is now handled by StartupVerifier,
    not by AppSettings. This allows config loading to succeed even
    when models haven't been downloaded yet.
    """
    (tmp_path / "stt.bin").touch()
    (tmp_path / "voice.onnx").touch()

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
    (tmp_path / "voice.onnx").touch()

    with pytest.raises(ValidationError) as excinfo:
        AppSettings(
            stt=STTSettings(model_path=str(tmp_path / "stt.bin")),
            llm=LLMSettings(model_path=str(tmp_path / "llm.gguf")),
            tts=TTSSettings(model_path=str(tmp_path / "voice.onnx")),
            speaker_a_key="space",
            speaker_b_key="space",  # Duplicate
        )
    assert "Speaker keys must be distinct" in str(excinfo.value)
