"""Smoke test fixtures with mocked models.

Provides fixtures for quick initialization tests that don't require
actual model downloads - uses mocks instead.
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.core.config import (
    STTSettings,
    LLMSettings,
    TTSSettings,
    AppSettings,
    SpeakerSettings,
)


@pytest.fixture
def mock_stt_model_path(tmp_path: Path) -> str:
    """Provide a mock path for STT model."""
    # Create the directory to pass validation
    model_dir = tmp_path / "mock_whisper_model"
    model_dir.mkdir(parents=True, exist_ok=True)
    return str(model_dir)


@pytest.fixture
def mock_llm_model_path(tmp_path: Path) -> str:
    """Provide a mock path for LLM model."""
    model_path = tmp_path / "mock_model.gguf"
    model_path.touch()  # Create empty file for path validation
    return str(model_path)


@pytest.fixture
def mock_tts_model_path(tmp_path: Path) -> str:
    """Provide a mock path for TTS model."""
    model_path = tmp_path / "mock_tts.onnx"
    model_path.touch()  # Create empty file for path validation
    json_path = tmp_path / "mock_tts.onnx.json"
    json_path.write_text("{}")
    return str(model_path)


@pytest.fixture
def stt_settings(mock_stt_model_path: str) -> STTSettings:
    """Create STT settings with mock path."""
    return STTSettings(
        model_path=mock_stt_model_path,
        language="en",
        device="cpu",
        compute_type="int8",
    )


@pytest.fixture
def llm_settings(mock_llm_model_path: str) -> LLMSettings:
    """Create LLM settings with mock path."""
    return LLMSettings(
        model_path=mock_llm_model_path,
        n_gpu_layers=0,
        context_window=2048,
        n_threads=2,
    )


@pytest.fixture
def tts_settings(mock_tts_model_path: str) -> TTSSettings:
    """Create TTS settings with mock path."""
    return TTSSettings(
        model_path=mock_tts_model_path,
        speaker_id=None,
    )


@pytest.fixture
def app_settings(
    mock_stt_model_path: str,
    mock_llm_model_path: str,
    mock_tts_model_path: str,
) -> AppSettings:
    """Create full app settings with mock paths."""
    return AppSettings(
        stt=STTSettings(
            model_path=mock_stt_model_path,
            language="en",
        ),
        llm=LLMSettings(
            model_path=mock_llm_model_path,
            n_gpu_layers=0,
        ),
        tts=TTSSettings(
            model_path=mock_tts_model_path,
        ),
        speakers={
            "a": SpeakerSettings(key="space", from_lang="en", to_lang="ru"),
            "b": SpeakerSettings(key="alt_r", from_lang="ru", to_lang="en"),
        },
    )


@pytest.fixture
def mock_whisper_model():
    """Create a mock WhisperModel."""
    mock = MagicMock()
    mock.transcribe.return_value = (
        iter([MagicMock(text="Hello world")]),
        MagicMock(language="en", language_probability=0.99),
    )
    return mock


@pytest.fixture
def mock_llama_model():
    """Create a mock Llama model."""
    mock = MagicMock()
    mock.create_chat_completion.return_value = {"choices": [{"message": {"content": "Привет мир"}}]}
    return mock


@pytest.fixture
def mock_piper_voice():
    """Create a mock PiperVoice."""
    mock_config = MagicMock()
    mock_config.sample_rate = 22050

    mock_chunk = MagicMock()
    mock_chunk.audio_int16_bytes = b"\x00\x00" * 1000  # Silence

    mock_voice = MagicMock()
    mock_voice.config = mock_config
    mock_voice.synthesize.return_value = iter([mock_chunk])

    return mock_voice
