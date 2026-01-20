import yaml
from pathlib import Path
from app.settings import load_settings, AppSettings


def test_load_settings_full_schema(tmp_path):
    """
    Test that load_settings correctly loads all configuration sections
    defined in the PRD (Audio, STT, LLM, TTS, Input).
    """
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
                "stt": {"model_path": "models/stt/test", "language": "en", "beam_size": 5},
                "llm": {"model_path": "models/llm/test.gguf", "n_ctx": 2048, "thread_count": 4},
                "tts": {"model_path": "models/tts/test.onnx", "speaker_id": 0},
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
    assert settings.stt.model_path == "models/stt/test"
    assert settings.stt.language == "en"

    # Assertions for LLM
    assert settings.llm.model_path == "models/llm/test.gguf"
    assert settings.llm.thread_count == 4

    # Assertions for TTS
    assert settings.tts.model_path == "models/tts/test.onnx"
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
