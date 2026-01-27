import pytest
from pydantic import ValidationError
from app.core.config import TTSSettings


def test_tts_settings_validation_file_not_found():
    """Test that model_path validation fails if file does not exist."""
    with pytest.raises(ValidationError) as excinfo:
        TTSSettings(model_path="non_existent_model.onnx")

    assert "not found" in str(excinfo.value)


def test_tts_settings_sample_rate_field():
    """Test that sample_rate field exists and defaults to None."""
    settings = TTSSettings(model_path=__file__)  # Use current file as a dummy existing file
    assert hasattr(settings, "sample_rate")
    assert settings.sample_rate is None


def test_tts_settings_sample_rate_set():
    """Test that sample_rate can be set."""
    settings = TTSSettings(model_path=__file__, sample_rate=22050)
    assert settings.sample_rate == 22050
