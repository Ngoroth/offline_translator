from app.core.config import load_settings
from pathlib import Path


def test_load_real_config():
    """
    Smoke test to verify that the actual config.yaml in the root directory
    can be loaded and validates against the AppSettings schema.
    """
    config_path = Path("config.yaml")
    assert config_path.exists(), "config.yaml not found in root"

    # This will raise ValidationError if config is invalid
    settings = load_settings(config_path)

    # Basic sanity checks on the loaded config
    assert settings.platform in ["auto", "windows", "linux", "rpi"]
    assert settings.input_mode in ["keyboard", "gpio", "evdev"]

    # Check paths
    assert settings.stt.model_path, "STT model path is empty"
    assert settings.llm.model_path, "LLM model path is empty"
    assert settings.tts.model_path, "TTS model path is empty"

    # Check dual speaker config
    assert settings.speaker_a_key
    assert settings.speaker_b_key
