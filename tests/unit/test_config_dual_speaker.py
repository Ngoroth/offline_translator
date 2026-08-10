from pathlib import Path
import yaml
from app.core.config import load_settings


def test_dual_speaker_config_fields(tmp_path: Path):
    """
    Test that AppSettings loads the dual speaker config from the 'speakers' dict.
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
                "speakers": {
                    "a": {
                        "key": "space",
                        "from_lang": "en",
                        "to_lang": "ru",
                        "tts_model": str(ru_voice),
                    },
                    "b": {
                        "key": "alt_r",
                        "from_lang": "ru",
                        "to_lang": "en",
                        "tts_model": str(en_voice),
                    },
                },
            }
        },
    }

    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    settings = load_settings(config_file)

    assert settings.speakers["a"].key == "space"
    assert settings.speakers["b"].key == "alt_r"
    assert settings.speakers["a"].from_lang == "en"
    assert settings.speakers["b"].from_lang == "ru"
    assert settings.speakers["a"].tts_model == str(ru_voice)
    assert settings.speakers["b"].tts_model == str(en_voice)
