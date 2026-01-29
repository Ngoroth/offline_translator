"""Smoke tests for pipeline wiring.

Tests that the TranslationPipeline correctly wires all services
and manages session lifecycle with mocked components.
"""

from unittest.mock import patch, MagicMock

import pytest

from app.core.config import AppSettings
from app.orchestrator.pipeline import TranslationPipeline
from tests.mocks.mock_audio import MockAudioRecorder, MockAudioPlayer


@pytest.mark.smoke
@pytest.mark.asyncio
class TestPipelineWiring:
    """Tests for pipeline service wiring."""

    @patch("app.services.tts.PiperVoice")
    @patch("app.services.tts.SynthesisConfig")
    @patch("app.services.llm.Llama")
    async def test_pipeline_connects_all_services(
        self,
        mock_llama: MagicMock,
        mock_synthesis_config: MagicMock,
        mock_piper_voice_class: MagicMock,
        app_settings: AppSettings,
        mock_piper_voice: MagicMock,
    ):
        """TranslationPipeline should wire STT, LLM, TTS services."""
        # Consume unused mocks
        _ = mock_llama, mock_synthesis_config
        # Setup mocks
        mock_piper_voice_class.load.return_value = mock_piper_voice

        from app.services.stt import STTService
        from app.services.llm import LLMService
        from app.services.tts import TTSService

        stt = STTService(app_settings.stt)
        llm = LLMService(app_settings.llm)
        tts = TTSService(app_settings.tts)
        recorder = MockAudioRecorder(sample_rate=16000)
        player = MockAudioPlayer(sample_rate=16000)

        pipeline = TranslationPipeline(
            settings=app_settings,
            stt=stt,
            llm=llm,
            tts=tts,
            recorder=recorder,
            player=player,
        )

        # Verify wiring
        assert pipeline.stt == stt
        assert pipeline.llm == llm
        assert pipeline.tts == tts
        assert pipeline.recorder == recorder
        assert pipeline.player == player
        assert pipeline.session_manager is not None

    @patch("app.services.tts.PiperVoice")
    @patch("app.services.tts.SynthesisConfig")
    @patch("app.services.llm.Llama")
    async def test_pipeline_injects_session_manager(
        self,
        mock_llama: MagicMock,
        mock_synthesis_config: MagicMock,
        mock_piper_voice_class: MagicMock,
        app_settings: AppSettings,
        mock_piper_voice: MagicMock,
    ):
        """Pipeline should inject SessionManager into all services."""
        _ = mock_llama, mock_synthesis_config
        mock_piper_voice_class.load.return_value = mock_piper_voice

        from app.services.stt import STTService
        from app.services.llm import LLMService
        from app.services.tts import TTSService

        stt = STTService(app_settings.stt)
        llm = LLMService(app_settings.llm)
        tts = TTSService(app_settings.tts)
        recorder = MockAudioRecorder(sample_rate=16000)
        player = MockAudioPlayer(sample_rate=16000)

        pipeline = TranslationPipeline(
            settings=app_settings,
            stt=stt,
            llm=llm,
            tts=tts,
            recorder=recorder,
            player=player,
        )

        # SessionManager should be injected into all services
        assert stt.session_manager == pipeline.session_manager
        assert llm.session_manager == pipeline.session_manager
        assert tts.session_manager == pipeline.session_manager

    @patch("app.services.tts.PiperVoice")
    @patch("app.services.tts.SynthesisConfig")
    @patch("app.services.llm.Llama")
    async def test_pipeline_queue_chain(
        self,
        mock_llama: MagicMock,
        mock_synthesis_config: MagicMock,
        mock_piper_voice_class: MagicMock,
        app_settings: AppSettings,
        mock_piper_voice: MagicMock,
    ):
        """Pipeline should have proper queue chain: stt→llm→tts→player."""
        _ = mock_llama, mock_synthesis_config
        mock_piper_voice_class.load.return_value = mock_piper_voice

        from app.services.stt import STTService
        from app.services.llm import LLMService
        from app.services.tts import TTSService

        stt = STTService(app_settings.stt)
        llm = LLMService(app_settings.llm)
        tts = TTSService(app_settings.tts)
        recorder = MockAudioRecorder(sample_rate=16000)
        player = MockAudioPlayer(sample_rate=16000)

        pipeline = TranslationPipeline(
            settings=app_settings,
            stt=stt,
            llm=llm,
            tts=tts,
            recorder=recorder,
            player=player,
        )

        # Verify all queues exist
        assert pipeline.stt_queue is not None
        assert pipeline.llm_queue is not None
        assert pipeline.tts_queue is not None
        assert pipeline.player_queue is not None

        # Verify queues are empty initially
        assert pipeline.stt_queue.empty()
        assert pipeline.llm_queue.empty()
        assert pipeline.tts_queue.empty()
        assert pipeline.player_queue.empty()


@pytest.mark.smoke
@pytest.mark.asyncio
class TestPipelineSessionManagement:
    """Tests for pipeline session lifecycle."""

    @patch("app.services.tts.PiperVoice")
    @patch("app.services.tts.SynthesisConfig")
    @patch("app.services.llm.Llama")
    async def test_session_manager_injection(
        self,
        mock_llama: MagicMock,
        mock_synthesis_config: MagicMock,
        mock_piper_voice_class: MagicMock,
        app_settings: AppSettings,
        mock_piper_voice: MagicMock,
    ):
        """SessionManager should be injected into services on pipeline creation."""
        _ = mock_llama, mock_synthesis_config
        mock_piper_voice_class.load.return_value = mock_piper_voice

        from app.services.stt import STTService
        from app.services.llm import LLMService
        from app.services.tts import TTSService

        stt = STTService(app_settings.stt)
        llm = LLMService(app_settings.llm)
        tts = TTSService(app_settings.tts)
        recorder = MockAudioRecorder(sample_rate=16000)
        player = MockAudioPlayer(sample_rate=16000)

        # Initially no session manager
        assert stt.session_manager is None
        assert llm.session_manager is None
        assert tts.session_manager is None

        pipeline = TranslationPipeline(
            settings=app_settings,
            stt=stt,
            llm=llm,
            tts=tts,
            recorder=recorder,
            player=player,
        )

        # After pipeline creation, session manager is injected
        assert stt.session_manager is not None
        assert llm.session_manager is not None
        assert tts.session_manager is not None
        assert stt.session_manager == pipeline.session_manager
