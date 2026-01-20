import numpy as np
from unittest.mock import MagicMock, patch
from app.services.stt import STTService
from app.services.translator import TranslatorService
from app.services.tts import TTSService


@patch("app.services.stt.WhisperModel")
@patch("app.services.translator.Llama")
@patch("app.services.tts.PiperVoice.load")
def test_full_pipeline(mock_piper_load, mock_llama, mock_whisper):
    """
    Test the full STT -> Translation -> TTS pipeline.
    """
    # 1. Mock STT
    mock_whisper_instance = mock_whisper.return_value
    mock_segment = MagicMock()
    mock_segment.text = "How are you?"
    mock_whisper_instance.transcribe.return_value = ([mock_segment], MagicMock())

    # 2. Mock Translator
    mock_llama_instance = mock_llama.return_value
    mock_llama_instance.create_chat_completion.return_value = {
        "choices": [{"message": {"content": "Как дела?"}}]
    }

    # 3. Mock TTS
    mock_voice = MagicMock()
    mock_piper_load.return_value = mock_voice
    mock_chunk = MagicMock()
    mock_chunk.audio_int16_array = np.zeros(8000, dtype=np.int16)
    mock_voice.synthesize.return_value = [mock_chunk]

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
def test_dual_ptt_logic(mock_piper_load, mock_llama, mock_whisper):
    """Test that different roles use different translation directions."""
    mock_llama_instance = mock_llama.return_value
    mock_llama_instance.create_chat_completion.return_value = {
        "choices": [{"message": {"content": "Hello"}}]
    }

    translator = TranslatorService(model_path="dummy")

    # Simulate Speaker B (Russian -> English)
    res = translator.translate("Привет", from_lang="Russian", to_lang="English")

    # Check that LLM was called with correct languages in prompt
    args, kwargs = mock_llama_instance.create_chat_completion.call_args
    messages = kwargs.get("messages")
    system_msg = messages[0]["content"]
    assert "from Russian to English" in system_msg
