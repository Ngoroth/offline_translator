import pytest
import numpy as np
from typing import Any
from unittest.mock import MagicMock, AsyncMock
from app.orchestrator.pipeline import TranslationPipeline


@pytest.mark.asyncio
async def test_dual_speaker_pipeline_flow():
    """
    Integration test verifying that Role A trigger results in:
    - Session created with En -> Ru
    - STT transcribed with En
    - LLM translated En -> Ru
    - TTS synthesized with Ru voice
    """
    # 1. Setup Mocks
    settings = MagicMock()
    settings.speakers = {
        "a": MagicMock(from_lang="en", to_lang="ru", tts_model="voice_ru"),
        "b": MagicMock(from_lang="ru", to_lang="en", tts_model="voice_en"),
    }
    settings.vad.aggressiveness = 3
    settings.vad.threshold_ms = 500
    settings.audio.sample_rate = 16000

    stt = AsyncMock()
    stt.transcribe.return_value = "Hello"

    llm = AsyncMock()
    llm.translate.return_value = "Privet"

    tts = MagicMock()

    # synthesize is a generator, need to mock return value
    async def mock_synthesize(*args: Any, **kwargs: Any):
        _ = args, kwargs
        yield b"audio_chunk"

    tts.synthesize.side_effect = mock_synthesize

    recorder = MagicMock()
    recorder.stop.return_value = np.zeros(16000, dtype=np.float32)  # 1 sec audio
    recorder.get_chunk = AsyncMock()  # Fix await error
    recorder.get_chunk.return_value = np.zeros(1024, dtype=np.float32)

    player = MagicMock()

    # 2. Initialize Pipeline
    pipeline = TranslationPipeline(
        settings=settings, stt=stt, llm=llm, tts=tts, recorder=recorder, player=player
    )

    # 3. Simulate Role A Trigger
    # start_session returns Session object
    session = await pipeline.start_session(role="a")
    assert session.source_lang == "en"
    assert session.target_lang == "ru"
    assert session.tts_voice == "voice_ru"

    # 4. Simulate Input Complete (PTT Release)
    # This triggers processing
    await pipeline.handle_input_complete()

    # 5. Wait for workers to finish
    # pipeline.wait_for_completion() waits for sentinels
    await pipeline.wait_for_completion()

    # 6. Verify Calls

    # STT: Should use source_lang="en"
    stt.transcribe.assert_called()
    _, kwargs = stt.transcribe.call_args
    assert kwargs["language"] == "en"
    assert kwargs["session_id"] == session.session_id

    # LLM: Should use En -> Ru
    llm.translate.assert_called()
    args, kwargs = llm.translate.call_args
    # signature: translate(text, source, target, session_id)
    # args[0] is text
    assert args[1] == "en"  # source
    assert args[2] == "ru"  # target
    assert kwargs["session_id"] == session.session_id

    # TTS: Should use Ru voice
    tts.synthesize.assert_called()
    args, kwargs = tts.synthesize.call_args
    assert kwargs["model_path"] == "voice_ru"
    assert kwargs["session_id"] == session.session_id

    # 7. Repeat for Role B
    session_b = await pipeline.start_session(role="b")
    assert session_b.source_lang == "ru"
    assert session_b.target_lang == "en"
    assert session_b.tts_voice == "voice_en"

    recorder.stop.return_value = np.zeros(16000, dtype=np.float32)
    stt.transcribe.return_value = "Privet"
    llm.translate.return_value = "Hello"

    await pipeline.handle_input_complete()
    await pipeline.wait_for_completion()

    # Verify B calls
    # STT: Ru
    _, kwargs = stt.transcribe.call_args
    assert kwargs["language"] == "ru"

    # LLM: Ru -> En
    args, kwargs = llm.translate.call_args
    assert args[1] == "ru"
    assert args[2] == "en"

    # TTS: En voice
    _, kwargs = tts.synthesize.call_args
    assert kwargs["model_path"] == "voice_en"
