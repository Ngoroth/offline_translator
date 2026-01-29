from pathlib import Path

from app.core.config import (
    AppSettings,
    VADSettings,
    STTSettings,
    LLMSettings,
    TTSSettings,
    SpeakerSettings,
)


def test_vad_settings_defaults(tmp_path: Path) -> None:
    # Create dummy model files for validation
    stt_dir = tmp_path / "stt_model"
    stt_dir.mkdir()
    llm_file = tmp_path / "model.gguf"
    llm_file.touch()
    tts_file = tmp_path / "tts.onnx"
    tts_file.touch()

    settings = AppSettings(
        stt=STTSettings(model_path=str(stt_dir)),
        llm=LLMSettings(model_path=str(llm_file)),
        tts=TTSSettings(model_path=str(tts_file)),
        speakers={"a": SpeakerSettings(from_lang="en", to_lang="es")},
    )
    assert settings.vad.threshold_ms == 500
    assert settings.vad.aggressiveness == 3


def test_vad_settings_custom(tmp_path: Path) -> None:
    # Create dummy model files for validation
    stt_dir = tmp_path / "stt_model"
    stt_dir.mkdir()
    llm_file = tmp_path / "model.gguf"
    llm_file.touch()
    tts_file = tmp_path / "tts.onnx"
    tts_file.touch()

    vad_data = VADSettings(threshold_ms=300, aggressiveness=1)
    settings = AppSettings(
        stt=STTSettings(model_path=str(stt_dir)),
        llm=LLMSettings(model_path=str(llm_file)),
        tts=TTSSettings(model_path=str(tts_file)),
        vad=vad_data,
        speakers={"a": SpeakerSettings(from_lang="en", to_lang="es")},
    )
    assert settings.vad.threshold_ms == 300
    assert settings.vad.aggressiveness == 1
