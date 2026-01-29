import pytest
import numpy as np
from unittest.mock import MagicMock, AsyncMock
from app.orchestrator.pipeline import TranslationPipeline


@pytest.mark.asyncio
async def test_tts_voice_selection_verification():
    """
    Test that the Pipeline actually requests synthesis with the correct voice model path.
    """
    # 1. Setup Config
    settings = MagicMock()
    settings.speaker_a_lang = "en"
    settings.speaker_b_lang = "ru"
    # Role A speaks En -> Ru (Output Voice: Ru)
    settings.speaker_b_voice = "voice_model_ru.onnx"
    # Role B speaks Ru -> En (Output Voice: En)
    settings.speaker_a_voice = "voice_model_en.onnx"
    settings.speakers = {}
    settings.vad.aggressiveness = 3
    settings.vad.threshold_ms = 500
    settings.audio.sample_rate = 16000

    # 2. Mock Services
    stt = AsyncMock()
    stt.transcribe.return_value = "Test Text"
    llm = AsyncMock()
    llm.translate.return_value = "Translated Text"

    tts = MagicMock()

    # Mock synthesize as async generator
    async def mock_synthesize(_text, _model_path=None, _session_id=None):
        yield b"audio"

    tts.synthesize.side_effect = mock_synthesize

    recorder = MagicMock()
    recorder.stop.return_value = np.zeros(16000, dtype=np.float32)
    recorder.get_chunk = AsyncMock(
        return_value=np.zeros(1024, dtype=np.float32)
    )  # Fix for vad worker

    player = MagicMock()

    pipeline = TranslationPipeline(
        settings=settings, stt=stt, llm=llm, tts=tts, recorder=recorder, player=player
    )

    # 3. Test Role A (En -> Ru)
    session_a = await pipeline.start_session(role="a")
    # Verify session configured correctly
    assert session_a.tts_voice == "voice_model_ru.onnx"

    # Run pipeline step
    await pipeline.handle_input_complete()
    await pipeline.wait_for_completion()

    # Verify TTS called with correct voice
    # We need to find the call with model_path="voice_model_ru.onnx"
    calls = tts.synthesize.call_args_list
    # Expected call: synthesize("Translated Text", model_path="voice_model_ru.onnx", session_id=...)
    # Check the last call or filter calls
    relevant_calls = [c for c in calls if c.kwargs.get("model_path") == "voice_model_ru.onnx"]
    assert len(relevant_calls) > 0, "TTS should have been called with Russian voice model"

    # 4. Test Role B (Ru -> En)
    # Reset mocks
    tts.synthesize.reset_mock()
    tts.synthesize.side_effect = mock_synthesize  # Reset side effect

    session_b = await pipeline.start_session(role="b")
    assert session_b.tts_voice == "voice_model_en.onnx"

    await pipeline.handle_input_complete()
    await pipeline.wait_for_completion()

    relevant_calls_b = [
        c
        for c in tts.synthesize.call_args_list
        if c.kwargs.get("model_path") == "voice_model_en.onnx"
    ]
    assert len(relevant_calls_b) > 0, "TTS should have been called with English voice model"
