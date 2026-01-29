from pathlib import Path
import yaml
from app.core.config import load_settings


def test_dual_speaker_config_fields(tmp_path: Path):
    """
    Test that AppSettings includes the required fields for dual speaker switching.
    """
    # Create dummy model files
    stt_model = tmp_path / "models/stt/test"
    stt_model.mkdir(parents=True, exist_ok=True)
    llm_model = tmp_path / "models/llm/test.gguf"
    llm_model.parent.mkdir(parents=True, exist_ok=True)
    llm_model.touch()
    tts_model = tmp_path / "models/tts/test.onnx"
    tts_model.parent.mkdir(parents=True, exist_ok=True)
    tts_model.touch()

    # Create voice model files for validation
    en_voice = tmp_path / "models/tts/en_voice.onnx"
    en_voice.touch()
    ru_voice = tmp_path / "models/tts/ru_voice.onnx"
    ru_voice.touch()

    config_data = {
        "current_profile": "dual_speaker_profile",
        "profiles": {
            "dual_speaker_profile": {
                "stt": {"model_path": str(stt_model)},
                "llm": {"model_path": str(llm_model)},
                "tts": {"model_path": str(tts_model)},
                # These are the new fields we expect, either at root or in a section.
                # The story implies they are top-level or easily accessible.
                # Let's try to define them at the profile level (AppSettings)
                "speaker_a_key": "space",
                "speaker_b_key": "alt_r",
                "speaker_a_lang": "en",
                "speaker_b_lang": "ru",
                "speaker_a_voice": str(en_voice),
                "speaker_b_voice": str(ru_voice),
            }
        },
    }

    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    # This should fail initially because fields don't exist
    settings = load_settings(config_file)

    assert settings.speaker_a_key == "space"
    assert settings.speaker_b_key == "alt_r"
    assert settings.speaker_a_lang == "en"
    assert settings.speaker_b_lang == "ru"
    assert settings.speaker_a_voice == str(en_voice)
    assert settings.speaker_b_voice == str(ru_voice)
