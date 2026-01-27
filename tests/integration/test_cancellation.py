import pytest
import asyncio
import numpy as np
from unittest.mock import MagicMock, patch, AsyncMock
from app.orchestrator.pipeline import TranslationPipeline
from app.services.stt import STTService
from app.services.llm import LLMService
from app.services.tts import TTSService
from app.core.config import AppSettings, STTSettings, LLMSettings, TTSSettings


@pytest.mark.asyncio
async def test_integration_cancellation_aborts_pipeline():
    # 1. Setup Mocks

    # Mock Settings
    settings = MagicMock()
    settings.vad.aggressiveness = 3
    settings.vad.threshold_ms = 500
    settings.audio.sample_rate = 16000
    settings.speakers = {}

    # Mock Recorder/Player
    recorder = MagicMock()
    recorder.sample_rate = 16000
    # recorder.stop() returns audio
    recorder.stop.return_value = np.zeros(16000, dtype=np.float32)

    player = MagicMock()

    # Mock STT Model (The slow part)
    with (
        patch("app.services.stt.WhisperModel") as mock_whisper_cls,
        patch("app.services.llm.Llama"),
        patch("app.services.tts.PiperVoice.load"),
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.is_file", return_value=True),
    ):
        mock_model = mock_whisper_cls.return_value

        # Define a slow transcribe function
        def slow_transcribe(*args, **kwargs):
            import time

            time.sleep(0.5)
            return (
                [MagicMock(text="Delayed Text")],
                MagicMock(language="en", language_probability=1.0),
            )

        mock_model.transcribe.side_effect = slow_transcribe

        # Initialize Services
        stt_service = STTService(STTSettings(model_path="dummy"))
        llm_service = LLMService(LLMSettings(model_path="dummy.gguf"))
        tts_service = TTSService(TTSSettings(model_path="dummy.onnx"))

        pipeline = TranslationPipeline(
            settings=settings,
            stt=stt_service,
            llm=llm_service,
            tts=tts_service,
            recorder=recorder,
            player=player,
        )

        # Start Session
        session = await pipeline.start_session()

        # Simulate Input
        await pipeline.handle_input_complete()

        # Wait small amount to ensure STT started but is sleeping
        await asyncio.sleep(0.1)

        # Cancel
        await pipeline.stop_session()

        # Wait for completion (tasks should end)
        await pipeline.wait_for_completion()

        # Verify STT called model
        mock_model.transcribe.assert_called()

        # Verify LLM Queue does NOT have the text
        items = []
        while not pipeline.llm_queue.empty():
            item = await pipeline.llm_queue.get()
            items.append(item)

        # Should contain only None (sentinel) or be empty
        for item in items:
            if item is not None:
                assert item["text"] != "Delayed Text", "Cancelled text leaked to LLM queue"

        # Also verify session is invalid
        assert not pipeline.session_manager.is_valid(session.session_id)
