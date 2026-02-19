from app.core.config import TTSSettings


def test_tts_settings_accepts_nonexistent_path():
    """Test that model_path accepts non-existent files.

    File existence validation is now handled by StartupVerifier,
    not by TTSSettings. This allows config loading to succeed even
    when models haven't been downloaded yet.
    """
    # Should NOT raise ValidationError - validation deferred to StartupVerifier
    settings = TTSSettings(model_path="non_existent_model.onnx")
    assert settings.model_path == "non_existent_model.onnx"


def test_tts_settings_sample_rate_field():
    """Test that sample_rate field exists and defaults to None."""
    settings = TTSSettings(model_path=__file__)  # Use current file as a dummy existing file
    assert hasattr(settings, "sample_rate")
    assert settings.sample_rate is None


def test_tts_settings_sample_rate_set():
    """Test that sample_rate can be set."""
    settings = TTSSettings(model_path=__file__, sample_rate=22050)
    assert settings.sample_rate == 22050
