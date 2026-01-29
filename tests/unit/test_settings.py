from pathlib import Path
import yaml
from app.core.config import load_settings, AppSettings


def test_load_settings_full_schema(tmp_path: Path):
    """
    Test that load_settings correctly loads all configuration sections
    defined in the PRD (Audio, STT, LLM, TTS, Input).
    """
    # Create dummy files for validation to pass
    stt_model = tmp_path / "models/stt/test"
    stt_model.mkdir(parents=True, exist_ok=True)

    llm_model = tmp_path / "models/llm/test.gguf"
    llm_model.parent.mkdir(parents=True, exist_ok=True)
    llm_model.touch()

    tts_model = tmp_path / "models/tts/test.onnx"
    tts_model.parent.mkdir(parents=True, exist_ok=True)
    tts_model.touch()

    config_data = {
        "current_profile": "test_profile",
        "profiles": {
            "test_profile": {
                "audio": {
                    "sample_rate": 44100,
                    "channels": 2,
                    "input_device_index": 1,
                    "output_device_index": 2,
                },
                "stt": {"model_path": str(stt_model), "language": "en", "beam_size": 5},
                "llm": {
                    "model_path": str(llm_model),
                    "context_window": 2048,
                    "n_threads": 4,
                },
                "tts": {"model_path": str(tts_model), "speaker_id": 0},
                "input": {"ptt_a": "space", "ptt_b": "alt"},
                "speakers": {
                    "a": {"from_lang": "English", "to_lang": "Russian"},
                    "b": {"from_lang": "Russian", "to_lang": "English"},
                },
            }
        },
    }

    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    settings = load_settings(config_file)

    # Assertions for Audio
    assert settings.audio.sample_rate == 44100
    assert settings.audio.channels == 2
    assert settings.audio.input_device_index == 1

    # Assertions for STT
    assert settings.stt.model_path == str(stt_model)
    assert settings.stt.language == "en"

    # Assertions for LLM
    assert settings.llm.model_path == str(llm_model)
    assert settings.llm.n_threads == 4

    # Assertions for TTS
    assert settings.tts.model_path == str(tts_model)
    assert settings.tts.speaker_id == 0

    # Assertions for Input
    assert settings.input.ptt_a == "space"
    assert settings.input.ptt_b == "alt"


def test_load_default_config_yaml():
    """Test that the project's actual config.yaml is valid and loadable."""
    root_dir = Path(__file__).parent.parent.parent
    config_path = root_dir / "config.yaml"

    assert config_path.exists()

    settings = load_settings(config_path)
    assert isinstance(settings, AppSettings)
    assert settings.stt.language == "en"
