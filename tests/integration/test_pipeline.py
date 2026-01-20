from typing import cast, Any
from unittest.mock import MagicMock, patch
import numpy as np
from app.services.stt import STTService
from app.services.translator import TranslatorService
from app.services.tts import TTSService


@patch("app.services.stt.WhisperModel")
@patch("app.services.translator.Llama")
@patch("app.services.tts.PiperVoice.load")
def test_full_pipeline(
    mock_piper_load: MagicMock, mock_llama: MagicMock, mock_whisper: MagicMock
) -> None:
    """
    Test the full STT -> Translation -> TTS pipeline.
    """
    # 1. Mock STT
    mock_whisper_instance: Any = mock_whisper.return_value
    mock_segment: Any = MagicMock()
    _ = setattr(mock_segment, "text", "How are you?")
    _ = setattr(
        mock_whisper_instance, "transcribe", MagicMock(return_value=([mock_segment], MagicMock()))
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
    mock_chunk: Any = MagicMock()
    _ = setattr(mock_chunk, "audio_int16_array", np.zeros(8000, dtype=np.int16))
    _ = setattr(mock_voice, "synthesize", MagicMock(return_value=[mock_chunk]))

    # Initialize services
    stt = STTService(model_path="dummy")
    translator = TranslatorService(model_path="dummy")
    tts = TTSService(model_path="dummy.onnx")

    # Run pipeline
    input_audio = np.zeros(16000, dtype=np.float32)

    # Step A: STT
    text = stt.transcribe(input_audio)
    assert text == "How are you?"

    # Step B: Translate (Speaker A)
    translation = translator.translate(text, "English", "Russian")
    assert translation == "Как дела?"

    # Step C: TTS
    output_audio = tts.synthesize(translation)
    assert isinstance(output_audio, np.ndarray)
    assert len(output_audio) == 8000


@patch("app.services.stt.WhisperModel")
@patch("app.services.translator.Llama")
@patch("app.services.tts.PiperVoice.load")
def test_dual_ptt_logic(
    _mock_piper_load: MagicMock, mock_llama: MagicMock, _mock_whisper: MagicMock
) -> None:
    """Test that different roles use different translation directions."""
    mock_llama_instance: Any = mock_llama.return_value
    _ = setattr(
        mock_llama_instance,
        "create_chat_completion",
        MagicMock(return_value={"choices": [{"message": {"content": "Hello"}}]}),
    )

    translator = TranslatorService(model_path="dummy")

    # Simulate Speaker B (Russian -> English)
    _ = translator.translate("Привет", from_lang="Russian", to_lang="English")

    # Check that LLM was called with correct languages in prompt
    call_args: Any = mock_llama_instance.create_chat_completion.call_args
    assert call_args is not None
    _, kwargs = cast(tuple[tuple[Any, ...], dict[str, Any]], call_args)
    messages = cast(list[dict[str, str]], kwargs.get("messages"))
    system_msg = messages[0]["content"]
    assert "from Russian to English" in system_msg
