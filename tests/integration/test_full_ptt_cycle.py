"""Integration tests for full PTT cycle.

Tests the complete Press-To-Talk flow with mocked services.
"""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.core.config import AppSettings, STTSettings, LLMSettings, TTSSettings
from app.orchestrator.pipeline import TranslationPipeline
from tests.mocks.mock_audio import MockAudioRecorder, MockAudioPlayer


@pytest.mark.integration
@pytest.mark.asyncio
class TestFullPTTCycle:
    """Tests for complete PTT cycle flow."""

    @patch("app.services.tts.PiperVoice")
    @patch("app.services.tts.SynthesisConfig")
    @patch("app.services.stt.WhisperModel")
    @patch("app.services.llm.Llama")
    async def test_start_session_language_config_speaker_a(
        self,
        mock_llama: MagicMock,
        mock_whisper: MagicMock,
        mock_synthesis_config: MagicMock,
        mock_piper_voice: MagicMock,
        tmp_path: Path,
    ):
        """Verify start_session() configures language for Speaker A: en→ru."""
        _ = mock_llama, mock_whisper, mock_synthesis_config

        # Setup mocks
        mock_voice = MagicMock()
        mock_voice.config.sample_rate = 22050
        mock_piper_voice.load.return_value = mock_voice

        # Create model files
        stt_path = tmp_path / "stt"
        stt_path.mkdir()
        llm_path = tmp_path / "llm.gguf"
        llm_path.touch()
        tts_path = tmp_path / "tts.onnx"
        tts_path.touch()
        (tmp_path / "tts.onnx.json").write_text("{}")

        from app.services.stt import STTService
        from app.services.llm import LLMService
        from app.services.tts import TTSService

        settings = AppSettings(
            stt=STTSettings(model_path=str(stt_path)),
            llm=LLMSettings(model_path=str(llm_path)),
            tts=TTSSettings(model_path=str(tts_path)),
            speaker_a_lang="en",
            speaker_b_lang="ru",
        )

        stt = STTService(settings.stt)
        llm = LLMService(settings.llm)
        tts = TTSService(settings.tts)
        recorder = MockAudioRecorder(sample_rate=16000)
        player = MockAudioPlayer(sample_rate=16000)

        pipeline = TranslationPipeline(
            settings=settings,
            stt=stt,
            llm=llm,
            tts=tts,
            recorder=recorder,
            player=player,
        )

        # Start session for Speaker A
        session = await pipeline.start_session(role="a")

        # Verify language configuration
        assert session.source_lang == "en"
        assert session.target_lang == "ru"

        # Cleanup
        await pipeline.stop_session()

    @patch("app.services.tts.PiperVoice")
    @patch("app.services.tts.SynthesisConfig")
    @patch("app.services.stt.WhisperModel")
    @patch("app.services.llm.Llama")
    async def test_start_session_language_config_speaker_b(
        self,
        mock_llama: MagicMock,
        mock_whisper: MagicMock,
        mock_synthesis_config: MagicMock,
        mock_piper_voice: MagicMock,
        tmp_path: Path,
    ):
        """Verify start_session() configures language for Speaker B: ru→en."""
        _ = mock_llama, mock_whisper, mock_synthesis_config

        mock_voice = MagicMock()
        mock_voice.config.sample_rate = 22050
        mock_piper_voice.load.return_value = mock_voice

        stt_path = tmp_path / "stt"
        stt_path.mkdir()
        llm_path = tmp_path / "llm.gguf"
        llm_path.touch()
        tts_path = tmp_path / "tts.onnx"
        tts_path.touch()
        (tmp_path / "tts.onnx.json").write_text("{}")

        from app.services.stt import STTService
        from app.services.llm import LLMService
        from app.services.tts import TTSService

        settings = AppSettings(
            stt=STTSettings(model_path=str(stt_path)),
            llm=LLMSettings(model_path=str(llm_path)),
            tts=TTSSettings(model_path=str(tts_path)),
            speaker_a_lang="en",
            speaker_b_lang="ru",
        )

        stt = STTService(settings.stt)
        llm = LLMService(settings.llm)
        tts = TTSService(settings.tts)
        recorder = MockAudioRecorder(sample_rate=16000)
        player = MockAudioPlayer(sample_rate=16000)

        pipeline = TranslationPipeline(
            settings=settings,
            stt=stt,
            llm=llm,
            tts=tts,
            recorder=recorder,
            player=player,
        )

        # Start session for Speaker B
        session = await pipeline.start_session(role="b")

        # Verify language configuration is reversed
        assert session.source_lang == "ru"
        assert session.target_lang == "en"

        # Cleanup
        await pipeline.stop_session()

    @patch("app.services.tts.PiperVoice")
    @patch("app.services.tts.SynthesisConfig")
    @patch("app.services.stt.WhisperModel")
    @patch("app.services.llm.Llama")
    async def test_handle_input_complete_flow(
        self,
        mock_llama: MagicMock,
        mock_whisper: MagicMock,
        mock_synthesis_config: MagicMock,
        mock_piper_voice: MagicMock,
        tmp_path: Path,
    ):
        """Verify handle_input_complete() triggers pipeline processing."""
        # Setup mocks
        mock_whisper_instance: Any = mock_whisper.return_value
        mock_segment = MagicMock()
        mock_segment.text = "Hello"
        mock_info = MagicMock()
        mock_info.language = "en"
        mock_info.language_probability = 0.99
        mock_whisper_instance.transcribe.return_value = ([mock_segment], mock_info)

        mock_llama_instance: Any = mock_llama.return_value
        mock_llama_instance.create_chat_completion.return_value = {
            "choices": [{"message": {"content": "Привет"}}]
        }

        _ = mock_synthesis_config

        mock_voice = MagicMock()
        mock_voice.config.sample_rate = 22050
        dummy_audio = np.zeros(1000, dtype=np.int16)
        mock_chunk = MagicMock()
        mock_chunk.audio_int16_bytes = dummy_audio.tobytes()
        mock_voice.synthesize.return_value = iter([mock_chunk])
        mock_piper_voice.load.return_value = mock_voice

        stt_path = tmp_path / "stt"
        stt_path.mkdir()
        llm_path = tmp_path / "llm.gguf"
        llm_path.touch()
        tts_path = tmp_path / "tts.onnx"
        tts_path.touch()
        (tmp_path / "tts.onnx.json").write_text("{}")

        from app.services.stt import STTService
        from app.services.llm import LLMService
        from app.services.tts import TTSService

        settings = AppSettings(
            stt=STTSettings(model_path=str(stt_path)),
            llm=LLMSettings(model_path=str(llm_path)),
            tts=TTSSettings(model_path=str(tts_path)),
        )

        stt = STTService(settings.stt)
        llm = LLMService(settings.llm)
        tts = TTSService(settings.tts)
        recorder = MockAudioRecorder(sample_rate=16000)
        player = MockAudioPlayer(sample_rate=16000)

        pipeline = TranslationPipeline(
            settings=settings,
            stt=stt,
            llm=llm,
            tts=tts,
            recorder=recorder,
            player=player,
        )

        # Start session and inject audio
        await pipeline.start_session(role="a")
        recorder.inject_chunk(np.zeros(16000, dtype=np.float32))

        # Handle input complete
        await pipeline.handle_input_complete()

        # Wait for completion
        await pipeline.wait_for_completion()

        # Verify STT was called
        assert mock_whisper_instance.transcribe.called

    @patch("app.services.tts.PiperVoice")
    @patch("app.services.tts.SynthesisConfig")
    @patch("app.services.stt.WhisperModel")
    @patch("app.services.llm.Llama")
    async def test_wait_for_completion_succeeds(
        self,
        mock_llama: MagicMock,
        mock_whisper: MagicMock,
        mock_synthesis_config: MagicMock,
        mock_piper_voice: MagicMock,
        tmp_path: Path,
    ):
        """Verify wait_for_completion() succeeds after processing."""
        # Setup minimal mocks
        mock_whisper_instance: Any = mock_whisper.return_value
        mock_whisper_instance.transcribe.return_value = (
            [],
            MagicMock(language="en", language_probability=0.99),
        )

        mock_llama_instance: Any = mock_llama.return_value
        mock_llama_instance.create_chat_completion.return_value = {
            "choices": [{"message": {"content": ""}}]
        }

        _ = mock_synthesis_config

        mock_voice = MagicMock()
        mock_voice.config.sample_rate = 22050
        mock_voice.synthesize.return_value = iter([])
        mock_piper_voice.load.return_value = mock_voice

        stt_path = tmp_path / "stt"
        stt_path.mkdir()
        llm_path = tmp_path / "llm.gguf"
        llm_path.touch()
        tts_path = tmp_path / "tts.onnx"
        tts_path.touch()
        (tmp_path / "tts.onnx.json").write_text("{}")

        from app.services.stt import STTService
        from app.services.llm import LLMService
        from app.services.tts import TTSService

        settings = AppSettings(
            stt=STTSettings(model_path=str(stt_path)),
            llm=LLMSettings(model_path=str(llm_path)),
            tts=TTSSettings(model_path=str(tts_path)),
        )

        stt = STTService(settings.stt)
        llm = LLMService(settings.llm)
        tts = TTSService(settings.tts)
        recorder = MockAudioRecorder(sample_rate=16000)
        player = MockAudioPlayer(sample_rate=16000)

        pipeline = TranslationPipeline(
            settings=settings,
            stt=stt,
            llm=llm,
            tts=tts,
            recorder=recorder,
            player=player,
        )

        await pipeline.start_session(role="a")
        await pipeline.handle_input_complete()

        # This should complete without error
        await pipeline.wait_for_completion()

        # Session should be cleared
        assert pipeline.session is None
