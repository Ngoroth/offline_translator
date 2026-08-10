"""Smoke tests for service initialization.

Tests that services can be initialized with mocked models.
These tests run quickly (~5s) and verify basic service wiring.
"""

from unittest.mock import patch, MagicMock

import pytest

from app.core.config import STTSettings, LLMSettings, TTSSettings
from app.services.stt import STTService
from app.services.llm import LLMService, LLMModelLoadError
from app.services.tts import TTSService
from tests.mocks.mock_input import MockInput
from tests.mocks.mock_audio import MockAudioRecorder, MockAudioPlayer


@pytest.mark.smoke
class TestSTTServiceInit:
    """Tests for STT service initialization."""

    def test_stt_service_init_with_mocked_model(self, stt_settings: STTSettings):
        """STTService should initialize without loading model (lazy loading)."""
        # STTService uses lazy loading, so init should succeed without model
        stt = STTService(settings=stt_settings)

        assert stt.settings == stt_settings
        assert stt._model is None
        assert stt.session_manager is None

    def test_stt_service_init_with_session_manager(self, stt_settings: STTSettings):
        """STTService should accept optional session manager."""
        mock_session_manager = MagicMock()
        stt = STTService(settings=stt_settings, session_manager=mock_session_manager)

        assert stt.session_manager == mock_session_manager


@pytest.mark.smoke
class TestLLMServiceInit:
    """Tests for LLM service initialization."""

    @patch("app.services.llm.Llama")
    def test_llm_service_init_with_mocked_model(
        self, mock_llama_class: MagicMock, llm_settings: LLMSettings
    ):
        """LLMService should initialize with mocked Llama model."""
        mock_model = MagicMock()
        mock_llama_class.return_value = mock_model

        llm = LLMService(settings=llm_settings)

        assert llm.settings == llm_settings
        assert llm._model == mock_model
        mock_llama_class.assert_called_once_with(
            model_path=llm_settings.model_path,
            n_ctx=llm_settings.context_window,
            n_threads=llm_settings.n_threads,
            n_gpu_layers=llm_settings.n_gpu_layers,
            verbose=False,
        )

    @patch("app.services.llm.Llama")
    def test_llm_service_init_failure_raises_error(
        self, mock_llama_class: MagicMock, llm_settings: LLMSettings
    ):
        """LLMService should raise LLMModelLoadError on init failure."""
        mock_llama_class.side_effect = Exception("Model load failed")

        with pytest.raises(LLMModelLoadError):
            LLMService(settings=llm_settings)

    @patch("app.services.llm.Llama")
    def test_llm_service_init_with_session_manager(
        self,
        mock_llama_class: MagicMock,
        llm_settings: LLMSettings,
    ):
        """LLMService should accept optional session manager."""
        _ = mock_llama_class  # Used by patch
        mock_session_manager = MagicMock()
        llm = LLMService(settings=llm_settings, session_manager=mock_session_manager)

        assert llm.session_manager == mock_session_manager


@pytest.mark.smoke
class TestTTSServiceInit:
    """Tests for TTS service initialization."""

    @patch("app.services.tts.PiperVoice")
    @patch("app.services.tts.SynthesisConfig")
    def test_tts_service_init_with_mocked_model(
        self,
        mock_synthesis_config: MagicMock,
        mock_piper_voice_class: MagicMock,
        tts_settings: TTSSettings,
        mock_piper_voice: MagicMock,
    ):
        """TTSService should initialize with mocked PiperVoice."""
        _ = mock_synthesis_config  # Used by patch
        mock_piper_voice_class.load.return_value = mock_piper_voice

        tts = TTSService(settings=tts_settings)

        assert tts.settings == tts_settings
        assert len(tts.voices) == 1
        assert tts.default_voice == mock_piper_voice

    @patch("app.services.tts.PiperVoice")
    @patch("app.services.tts.SynthesisConfig")
    def test_tts_service_init_with_session_manager(
        self,
        mock_synthesis_config: MagicMock,
        mock_piper_voice_class: MagicMock,
        tts_settings: TTSSettings,
        mock_piper_voice: MagicMock,
    ):
        """TTSService should accept optional session manager."""
        _ = mock_synthesis_config  # Used by patch
        mock_piper_voice_class.load.return_value = mock_piper_voice
        mock_session_manager = MagicMock()

        tts = TTSService(settings=tts_settings, session_manager=mock_session_manager)

        assert tts.session_manager == mock_session_manager


@pytest.mark.smoke
class TestMockInputInit:
    """Tests for MockInput initialization."""

    def test_mock_input_start(self):
        """MockInput.start() should succeed."""
        mock_input = MockInput()
        mock_input.start()  # Should not raise

        assert mock_input.pressed["a"] is False
        assert mock_input.pressed["b"] is False

    def test_mock_input_trigger_press_release(self):
        """MockInput should track press/release states."""
        mock_input = MockInput()

        mock_input.trigger_press("a")
        assert mock_input.pressed["a"] is True

        mock_input.trigger_release("a")
        assert mock_input.pressed["a"] is False


@pytest.mark.smoke
@pytest.mark.asyncio
class TestAudioComponentsInit:
    """Tests for audio recorder/player initialization."""

    async def test_mock_audio_recorder_init(self):
        """MockAudioRecorder should initialize with sample rate."""
        recorder = MockAudioRecorder(sample_rate=16000)

        assert recorder.sample_rate == 16000

    async def test_mock_audio_player_init(self):
        """MockAudioPlayer should initialize with sample rate."""
        player = MockAudioPlayer(sample_rate=16000)

        assert player.sample_rate == 16000
