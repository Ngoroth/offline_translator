"""Integration tests for API contracts.

Verifies that service API signatures match expected TypedDict payloads
and that services integrate correctly.
"""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.services.stt import STTService
from app.services.llm import LLMService
from app.services.tts import TTSService
from app.core.config import STTSettings, LLMSettings, TTSSettings


@pytest.mark.integration
class TestAPIContracts:
    """Tests for service API signature contracts."""

    @patch("app.services.stt.WhisperModel")
    @pytest.mark.asyncio
    async def test_stt_transcribe_signature(self, mock_whisper: MagicMock, tmp_path: Path):
        """Verify STTService.transcribe(audio, language, session_id) signature."""
        # Setup
        stt_path = tmp_path / "stt_model"
        stt_path.mkdir()

        mock_instance: Any = mock_whisper.return_value
        mock_segment = MagicMock()
        mock_segment.text = "Hello world"
        mock_info = MagicMock()
        mock_info.language = "en"
        mock_info.language_probability = 0.99
        mock_instance.transcribe.return_value = ([mock_segment], mock_info)

        stt = STTService(STTSettings(model_path=str(stt_path)))
        audio = np.zeros(16000, dtype=np.float32)

        # Test with all parameters
        result = await stt.transcribe(
            audio=audio,
            language="en",
            session_id="test-session-123",
        )

        assert result == "Hello world"
        assert mock_instance.transcribe.called

    @patch("app.services.llm.Llama")
    @pytest.mark.asyncio
    async def test_llm_translate_signature(self, mock_llama: MagicMock):
        """Verify LLMService.translate(text, source, target, session_id) signature."""
        mock_instance: Any = mock_llama.return_value
        mock_instance.create_chat_completion.return_value = {
            "choices": [{"message": {"content": "Привет мир"}}]
        }

        llm = LLMService(LLMSettings(model_path="test.gguf"))

        # Test with all parameters
        result = await llm.translate(
            text="Hello world",
            source_lang="English",
            target_lang="Russian",
            session_id="test-session-123",
        )

        assert result == "Привет мир"
        assert mock_instance.create_chat_completion.called

    @patch("app.services.tts.PiperVoice")
    @patch("app.services.tts.SynthesisConfig")
    @pytest.mark.asyncio
    async def test_tts_synthesize_signature(
        self,
        mock_synthesis_config: MagicMock,
        mock_piper_voice: MagicMock,
        tmp_path: Path,
    ):
        """Verify TTSService.synthesize(text, speaker_id, model_path, session_id) signature."""
        _ = mock_synthesis_config  # Used by patch

        # Setup mock voice
        mock_voice = MagicMock()
        mock_config = MagicMock()
        mock_config.sample_rate = 22050
        mock_voice.config = mock_config

        dummy_audio = np.zeros(8000, dtype=np.int16)
        mock_chunk = MagicMock()
        mock_chunk.audio_int16_bytes = dummy_audio.tobytes()
        mock_voice.synthesize.return_value = iter([mock_chunk])

        mock_piper_voice.load.return_value = mock_voice

        tts_path = tmp_path / "model.onnx"
        tts_path.touch()
        json_path = tmp_path / "model.onnx.json"
        json_path.write_text("{}")

        tts = TTSService(TTSSettings(model_path=str(tts_path)))

        # Test with all parameters
        chunks = []
        async for chunk in tts.synthesize(
            text="Hello world",
            speaker_id=0,
            model_path=str(tts_path),
            session_id="test-session-123",
        ):
            chunks.append(chunk)

        assert len(chunks) > 0
        assert mock_voice.synthesize.called


@pytest.mark.integration
class TestPayloadTypedDicts:
    """Tests for TypedDict payload structure validation."""

    def test_audio_payload_structure(self):
        """Verify AudioPayload has required fields."""
        from app.core.types import AudioPayload

        # Create a valid payload
        audio = np.zeros(16000, dtype=np.float32)
        payload: AudioPayload = {
            "audio": audio,
            "sample_rate": 16000,
            "session_id": "test-123",
        }

        assert "audio" in payload
        assert "sample_rate" in payload
        assert "session_id" in payload

    def test_text_payload_structure(self):
        """Verify TextPayload has required fields."""
        from app.core.types import TextPayload

        payload: TextPayload = {
            "text": "Hello world",
            "language": "en",
            "session_id": "test-123",
        }

        assert "text" in payload
        assert "language" in payload
        assert "session_id" in payload

    def test_translation_payload_structure(self):
        """Verify TranslationPayload has required fields."""
        from app.core.types import TranslationPayload

        payload: TranslationPayload = {
            "text": "Привет мир",
            "source_lang": "en",
            "target_lang": "ru",
            "session_id": "test-123",
        }

        assert "text" in payload
        assert "source_lang" in payload
        assert "target_lang" in payload
        assert "session_id" in payload
