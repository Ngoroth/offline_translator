from pathlib import Path
from typing import cast, Any
from unittest.mock import MagicMock, patch
import numpy as np
import pytest
from app.services.stt import STTService
from app.services.llm import LLMService
from app.services.tts import TTSService
from app.core.config import STTSettings, LLMSettings, TTSSettings


@pytest.mark.asyncio
@patch("app.services.stt.WhisperModel")
@patch("app.services.llm.Llama")
@patch("app.services.tts.PiperVoice.load")
async def test_full_pipeline(
    mock_piper_load: MagicMock, mock_llama: MagicMock, mock_whisper: MagicMock, tmp_path: Path
) -> None:
    """
    Test the full STT -> Translation -> TTS pipeline.
    """
    # Create dummy model files
    stt_path = tmp_path / "dummy_stt"
    stt_path.mkdir()
    llm_path = tmp_path / "dummy.gguf"
    llm_path.touch()
    tts_path = tmp_path / "dummy.onnx"
    tts_path.touch()

    # 1. Mock STT
    mock_whisper_instance: Any = mock_whisper.return_value
    mock_segment: Any = MagicMock()
    _ = setattr(mock_segment, "text", "How are you?")

    mock_info: Any = MagicMock()
    mock_info.language = "en"
    mock_info.language_probability = 0.99

    _ = setattr(
        mock_whisper_instance, "transcribe", MagicMock(return_value=([mock_segment], mock_info))
    )

    # 2. Mock Translator
    mock_llama_instance: Any = mock_llama.return_value
    _ = setattr(
        mock_llama_instance,
        "create_chat_completion",
        MagicMock(return_value={"choices": [{"message": {"content": "Как дела?"}}]}),
    )

    # 3. Mock TTS
    mock_voice: Any = MagicMock()
    _ = setattr(mock_piper_load, "return_value", mock_voice)

    # Create valid int16 bytes
    dummy_audio = np.zeros(8000, dtype=np.int16)
    dummy_bytes = dummy_audio.tobytes()

    # Mock Chunk object with audio_int16_bytes
    mock_chunk = MagicMock()
    mock_chunk.audio_int16_bytes = dummy_bytes

    # Mock synthesize to return iterator of Chunks
    _ = setattr(mock_voice, "synthesize", MagicMock(return_value=iter([mock_chunk])))

    # Also mock config.sample_rate
    mock_config = MagicMock()
    mock_config.sample_rate = 16000
    _ = setattr(mock_voice, "config", mock_config)

    # Initialize services
    stt = STTService(STTSettings(model_path=str(stt_path)))
    llm = LLMService(LLMSettings(model_path=str(llm_path)))
    tts = TTSService(TTSSettings(model_path=str(tts_path)))

    # Run pipeline
    input_audio = np.zeros(16000, dtype=np.float32)

    # Step A: STT
    text = await stt.transcribe(input_audio)
    assert text == "How are you?"

    # Step B: Translate (Speaker A)
    translation = await llm.translate(text, "English", "Russian")
    assert translation == "Как дела?"

    # Step C: TTS
    # Consume async generator
    output_audio_bytes = b""
    async for chunk in tts.synthesize(translation):
        output_audio_bytes += chunk

    assert len(output_audio_bytes) > 0


@pytest.mark.asyncio
@patch("app.services.stt.WhisperModel")
@patch("app.services.llm.Llama")
@patch("app.services.tts.PiperVoice.load")
async def test_dual_ptt_logic(
    _mock_piper_load: MagicMock, mock_llama: MagicMock, _mock_whisper: MagicMock
) -> None:
    """Test that different roles use different translation directions."""
    mock_llama_instance: Any = mock_llama.return_value
    _ = setattr(
        mock_llama_instance,
        "create_chat_completion",
        MagicMock(return_value={"choices": [{"message": {"content": "Hello"}}]}),
    )

    llm = LLMService(LLMSettings(model_path="dummy.gguf"))

    # Simulate Speaker B (Russian -> English)
    _ = await llm.translate("Привет", source_lang="Russian", target_lang="English")

    # Check that LLM was called with correct languages in prompt
    call_args: Any = mock_llama_instance.create_chat_completion.call_args
    assert call_args is not None
    _, kwargs = cast(tuple[tuple[Any, ...], dict[str, Any]], call_args)
    messages = cast(list[dict[str, str]], kwargs.get("messages"))
    system_msg = messages[0]["content"]
    assert "from Russian to English" in system_msg
