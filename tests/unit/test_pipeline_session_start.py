import pytest
from unittest.mock import MagicMock
from app.orchestrator.pipeline import TranslationPipeline
from app.orchestrator.session import Session


@pytest.mark.asyncio
async def test_pipeline_start_session_config():
    """
    Verify that start_session retrieves correct language/voice from config
    based on the role ('a' or 'b').
    """
    # Mock Settings
    settings = MagicMock()
    # Speaker A: En -> Ru (Voice Ru)
    settings.speakers = {
        "a": MagicMock(from_lang="en", to_lang="ru", tts_model="voice_ru"),
        "b": MagicMock(from_lang="ru", to_lang="en", tts_model="voice_en"),
    }
    settings.vad.aggressiveness = 3
    settings.vad.threshold_ms = 500
    settings.audio.sample_rate = 16000

    # Mock Services
    stt = MagicMock()
    llm = MagicMock()
    tts = MagicMock()
    recorder = MagicMock()
    player = MagicMock()

    # Instantiate Pipeline
    pipeline = TranslationPipeline(
        settings=settings, stt=stt, llm=llm, tts=tts, recorder=recorder, player=player
    )

    # Mock SessionManager
    pipeline.session_manager = MagicMock()
    pipeline.session_manager.start_session.return_value = Session(
        source_lang="en", target_lang="ru", tts_voice="voice_ru"
    )

    # Act - Start Session A
    await pipeline.start_session(role="a")

    # Assert A
    pipeline.session_manager.start_session.assert_called_with(
        source_lang="en", target_lang="ru", tts_voice="voice_ru"
    )

    # Act - Start Session B
    pipeline.session_manager.start_session.return_value = Session(
        source_lang="ru", target_lang="en", tts_voice="voice_en"
    )
    await pipeline.start_session(role="b")

    # Assert B - for role "b", target is speakers["b"].to_lang (en), so voice should be speakers["b"].tts_model
    pipeline.session_manager.start_session.assert_called_with(
        source_lang="ru", target_lang="en", tts_voice="voice_en"
    )
