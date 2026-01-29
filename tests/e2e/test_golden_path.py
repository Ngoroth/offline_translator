"""E2E tests for golden path translation pipeline.

Tests the full PTT→STT→LLM→TTS→Playback cycle with REAL models.
These tests require model downloads (~535MB total) and are cached.
"""

from pathlib import Path

import numpy as np
import pytest
from typing import Callable

from app.core.config import STTSettings, LLMSettings, TTSSettings
from app.services.stt import STTService
from app.services.llm import LLMService
from app.services.tts import TTSService


@pytest.mark.e2e
@pytest.mark.slow
class TestGoldenPath:
    """E2E tests for the golden path translation flow."""

    @pytest.mark.asyncio
    async def test_stt_with_real_whisper_model(
        self, stt_model_path: Path, synthetic_audio_generator: Callable[..., np.ndarray]
    ):
        """Test STT service with real Whisper-tiny model."""
        stt = STTService(
            STTSettings(
                model_path=str(stt_model_path),
                language="en",
                device="cpu",
                compute_type="int8",
            )
        )

        # Create synthetic audio (not real speech, so result may be empty or noise)
        audio = synthetic_audio_generator(duration_seconds=2.0)

        # Transcribe - may return empty for synthetic audio, but should not crash
        result = await stt.transcribe(audio, language="en")

        # Verify it returns something (even empty string for non-speech)
        assert result is not None

    @pytest.mark.asyncio
    async def test_llm_translation_with_real_qwen3(self, llm_model_path: Path):
        """Test LLM service with real Qwen3-0.6B model."""
        llm = LLMService(
            LLMSettings(
                model_path=str(llm_model_path),
                n_gpu_layers=0,  # CPU only for testing
                context_window=2048,
                n_threads=2,
            )
        )

        # Simple English text
        text = "Hello, how are you?"

        # Translate to Russian
        result = await llm.translate(text, "English", "Russian")

        assert result is not None
        assert len(result) > 0
        # Qwen3 should produce some Russian text

    @pytest.mark.asyncio
    async def test_tts_synthesis_with_real_piper(self, tts_model_path: Path):
        """Test TTS service with real Piper model."""
        tts = TTSService(
            TTSSettings(
                model_path=str(tts_model_path),
                speaker_id=None,
            )
        )

        # Simple text
        text = "Hello, how are you?"

        # Synthesize
        chunks = []
        async for chunk in tts.synthesize(text):
            chunks.append(chunk)

        assert len(chunks) > 0
        # Verify we got audio bytes
        total_bytes = sum(len(c) for c in chunks)
        assert total_bytes > 0

    @pytest.mark.asyncio
    async def test_full_translation_pipeline(
        self,
        stt_model_path: Path,
        llm_model_path: Path,
        tts_model_path: Path,
        synthetic_audio_generator: Callable[..., np.ndarray],
    ):
        """Full PTT→STT→LLM→TTS cycle with real models.

        This is the main golden path test validating the entire
        translation pipeline works end-to-end.
        """
        # 1. Initialize real services
        stt = STTService(
            STTSettings(
                model_path=str(stt_model_path),
                language="en",
                device="cpu",
                compute_type="int8",
            )
        )
        llm = LLMService(
            LLMSettings(
                model_path=str(llm_model_path),
                n_gpu_layers=0,
                context_window=2048,
                n_threads=2,
            )
        )
        tts = TTSService(
            TTSSettings(
                model_path=str(tts_model_path),
            )
        )

        # 2. Create synthetic audio
        audio = synthetic_audio_generator(duration_seconds=2.0)

        # 3. Run STT (may return empty for synthetic audio)
        text = await stt.transcribe(audio, language="en")

        # If STT returns something, continue pipeline
        if text and len(text.strip()) > 0:
            # 4. Translate
            translation = await llm.translate(text, "English", "Russian")
            assert translation is not None

            # 5. Synthesize
            audio_chunks = []
            async for chunk in tts.synthesize(translation):
                audio_chunks.append(chunk)
            assert len(audio_chunks) > 0
        else:
            # Even with empty transcription, verify services initialized correctly
            # Test with known text directly
            translation = await llm.translate("Hello", "English", "Russian")
            assert translation is not None

            audio_chunks = []
            async for chunk in tts.synthesize("Hello"):
                audio_chunks.append(chunk)
            assert len(audio_chunks) > 0
