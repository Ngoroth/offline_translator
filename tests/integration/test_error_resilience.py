"""Integration tests for error resilience.

Tests NFR6: Zero crash on phrase error - verifies that individual
service failures don't crash the pipeline.
"""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.core.config import AppSettings, STTSettings, LLMSettings, TTSSettings, SpeakerSettings
from app.orchestrator.pipeline import TranslationPipeline
from tests.mocks.mock_audio import MockAudioRecorder, MockAudioPlayer


@pytest.mark.integration
@pytest.mark.asyncio
class TestErrorResilience:
    """Tests for NFR6: Zero crash on phrase error."""

    @patch("app.services.tts.PiperVoice")
    @patch("app.services.tts.SynthesisConfig")
    @patch("app.services.stt.WhisperModel")
    @patch("app.services.llm.Llama")
    async def test_stt_failure_doesnt_crash_pipeline(
        self,
        mock_llama: MagicMock,
        mock_whisper: MagicMock,
        mock_synthesis_config: MagicMock,
        mock_piper_voice: MagicMock,
        tmp_path: Path,
    ):
        """STT failure should not crash the pipeline (NFR6)."""
        _ = mock_llama  # Suppress unused parameter warning
        # Setup STT to raise an exception
        mock_whisper_instance: Any = mock_whisper.return_value
        mock_whisper_instance.transcribe.side_effect = Exception("STT failed")

        # Setup other mocks minimally
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
            speakers={
                "a": SpeakerSettings(
                    key="space", from_lang="en", to_lang="ru", tts_model=str(tts_path)
                ),
                "b": SpeakerSettings(
                    key="alt_r", from_lang="ru", to_lang="en", tts_model=str(tts_path)
                ),
            },
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

        # This should NOT crash despite STT failure
        await pipeline.handle_input_complete()
        await pipeline.wait_for_completion()

        # Pipeline should still be functional
        assert pipeline.session is None

    @patch("app.services.tts.PiperVoice")
    @patch("app.services.tts.SynthesisConfig")
    @patch("app.services.stt.WhisperModel")
    @patch("app.services.llm.Llama")
    async def test_llm_failure_doesnt_crash_pipeline(
        self,
        mock_llama: MagicMock,
        mock_whisper: MagicMock,
        mock_synthesis_config: MagicMock,
        mock_piper_voice: MagicMock,
        tmp_path: Path,
    ):
        """LLM failure should not crash the pipeline (NFR6)."""
        # Setup STT to succeed
        mock_whisper_instance: Any = mock_whisper.return_value
        mock_segment = MagicMock()
        mock_segment.text = "Hello"
        mock_info = MagicMock()
        mock_info.language = "en"
        mock_info.language_probability = 0.99
        mock_whisper_instance.transcribe.return_value = ([mock_segment], mock_info)

        # Setup LLM to fail
        mock_llama_instance: Any = mock_llama.return_value
        mock_llama_instance.create_chat_completion.side_effect = Exception("LLM failed")

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
            speakers={
                "a": SpeakerSettings(
                    key="space", from_lang="en", to_lang="ru", tts_model=str(tts_path)
                ),
                "b": SpeakerSettings(
                    key="alt_r", from_lang="ru", to_lang="en", tts_model=str(tts_path)
                ),
            },
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
        recorder.inject_chunk(np.zeros(16000, dtype=np.float32))

        # This should NOT crash despite LLM failure
        await pipeline.handle_input_complete()
        await pipeline.wait_for_completion()

        assert pipeline.session is None

    @patch("app.services.tts.PiperVoice")
    @patch("app.services.tts.SynthesisConfig")
    @patch("app.services.stt.WhisperModel")
    @patch("app.services.llm.Llama")
    async def test_tts_failure_doesnt_crash_pipeline(
        self,
        mock_llama: MagicMock,
        mock_whisper: MagicMock,
        mock_synthesis_config: MagicMock,
        mock_piper_voice: MagicMock,
        tmp_path: Path,
    ):
        """TTS failure should not crash the pipeline (NFR6)."""
        # Setup STT to succeed
        mock_whisper_instance: Any = mock_whisper.return_value
        mock_segment = MagicMock()
        mock_segment.text = "Hello"
        mock_info = MagicMock()
        mock_info.language = "en"
        mock_info.language_probability = 0.99
        mock_whisper_instance.transcribe.return_value = ([mock_segment], mock_info)

        # Setup LLM to succeed
        mock_llama_instance: Any = mock_llama.return_value
        mock_llama_instance.create_chat_completion.return_value = {
            "choices": [{"message": {"content": "Привет"}}]
        }

        _ = mock_synthesis_config

        # Setup TTS to fail during synthesis
        mock_voice = MagicMock()
        mock_voice.config.sample_rate = 22050

        def failing_synthesize(*args: Any, **kwargs: Any):
            _ = args, kwargs
            raise Exception("TTS failed")

        mock_voice.synthesize.side_effect = failing_synthesize
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
            speakers={
                "a": SpeakerSettings(
                    key="space", from_lang="en", to_lang="ru", tts_model=str(tts_path)
                ),
                "b": SpeakerSettings(
                    key="alt_r", from_lang="ru", to_lang="en", tts_model=str(tts_path)
                ),
            },
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
        recorder.inject_chunk(np.zeros(16000, dtype=np.float32))

        # This should NOT crash despite TTS failure
        await pipeline.handle_input_complete()
        await pipeline.wait_for_completion()

        assert pipeline.session is None

    @patch("app.services.tts.PiperVoice")
    @patch("app.services.tts.SynthesisConfig")
    @patch("app.services.stt.WhisperModel")
    @patch("app.services.llm.Llama")
    async def test_barge_in_cleanup(
        self,
        mock_llama: MagicMock,
        mock_whisper: MagicMock,
        mock_synthesis_config: MagicMock,
        mock_piper_voice: MagicMock,
        tmp_path: Path,
    ):
        """Barge-in should cleanly cancel current session."""
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
            speakers={
                "a": SpeakerSettings(
                    key="space", from_lang="en", to_lang="ru", tts_model=str(tts_path)
                ),
                "b": SpeakerSettings(
                    key="alt_r", from_lang="ru", to_lang="en", tts_model=str(tts_path)
                ),
            },
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

        # Start first session
        session1 = await pipeline.start_session(role="a")
        session1_id = session1.session_id

        # Trigger barge-in (simulates new PTT press during playback)
        await pipeline.handle_barge_in()

        # Session should be cancelled
        assert pipeline.session is None

        # Start new session (should work cleanly)
        session2 = await pipeline.start_session(role="b")
        assert session2.session_id != session1_id
        assert session2.source_lang == "ru"  # Speaker B

        # Cleanup
        await pipeline.stop_session()
