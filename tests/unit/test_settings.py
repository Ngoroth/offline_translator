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
                "speakers": {
                    "a": {
                        "key": "space",
                        "from_lang": "en",
                        "to_lang": "ru",
                        "tts_model": str(tts_model),
                    },
                    "b": {
                        "key": "alt",
                        "from_lang": "ru",
                        "to_lang": "en",
                        "tts_model": str(tts_model),
                    },
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


def test_load_default_config_yaml():
    """Test that the project's actual config.yaml is valid and loadable."""
    root_dir = Path(__file__).parent.parent.parent
    config_path = root_dir / "config.yaml"

    assert config_path.exists()

    settings = load_settings(config_path)
    assert isinstance(settings, AppSettings)
    assert settings.stt.language == "en"


def test_load_settings_profile_override_takes_precedence_and_is_read_only(tmp_path: Path):
    config_data = {
        "current_profile": "desktop_rtx4070",
        "profiles": {
            "desktop_rtx4070": {
                "platform": "windows",
                "input_mode": "keyboard",
                "stt": {"model_path": "models/stt/desktop", "language": "en", "beam_size": 5},
                "llm": {
                    "model_path": "models/llm/desktop.gguf",
                    "context_window": 2048,
                    "n_threads": 4,
                },
                "tts": {"model_path": "models/tts/desktop.onnx", "speaker_id": 0},
            },
            "rpi_deployment": {
                "platform": "linux",
                "input_mode": "evdev",
                "stt": {"model_path": "models/stt/pi", "language": "ru", "beam_size": 3},
                "llm": {
                    "model_path": "models/llm/pi.gguf",
                    "context_window": 1024,
                    "n_threads": 2,
                },
                "tts": {"model_path": "models/tts/pi.onnx", "speaker_id": 1},
            },
        },
    }

    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump(config_data), encoding="utf-8")
    original_bytes = config_file.read_bytes()

    settings = load_settings(config_file, profile_override="rpi_deployment")

    assert settings.platform == "linux"
    assert settings.input_mode == "evdev"
    assert settings.stt.language == "ru"
    assert config_file.read_bytes() == original_bytes


def test_load_settings_profile_override_unknown_profile_lists_available(tmp_path: Path):
    config_data = {
        "current_profile": "desktop_rtx4070",
        "profiles": {
            "desktop_rtx4070": {
                "stt": {"model_path": "models/stt/desktop", "language": "en", "beam_size": 5},
                "llm": {
                    "model_path": "models/llm/desktop.gguf",
                    "context_window": 2048,
                    "n_threads": 4,
                },
                "tts": {"model_path": "models/tts/desktop.onnx", "speaker_id": 0},
            },
            "rpi_deployment": {
                "stt": {"model_path": "models/stt/pi", "language": "ru", "beam_size": 3},
                "llm": {
                    "model_path": "models/llm/pi.gguf",
                    "context_window": 1024,
                    "n_threads": 2,
                },
                "tts": {"model_path": "models/tts/pi.onnx", "speaker_id": 1},
            },
        },
    }

    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump(config_data), encoding="utf-8")

    try:
        load_settings(config_file, profile_override="missing_profile")
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected load_settings to raise ValueError for unknown profile")

    assert "missing_profile" in message
    assert "desktop_rtx4070" in message
    assert "rpi_deployment" in message
