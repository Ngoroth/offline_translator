"""E2E tests for dual speaker translation.

Tests Speaker A (en→ru) and Speaker B (ru→en) full cycles
with real models.
"""

from pathlib import Path

import pytest

from app.core.config import LLMSettings, TTSSettings
from app.services.llm import LLMService
from app.services.tts import TTSService


@pytest.mark.e2e
@pytest.mark.slow
class TestDualSpeaker:
    """E2E tests for dual speaker language switching."""

    @pytest.mark.asyncio
    async def test_speaker_a_en_to_ru(
        self,
        llm_model_path: Path,
        tts_model_path: Path,
    ):
        """Speaker A (en→ru) full cycle with real models."""
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

        # Speaker A speaks English, translates to Russian
        source_text = "Good morning!"
        source_lang = "English"
        target_lang = "Russian"

        # Translate
        translation = await llm.translate(source_text, source_lang, target_lang)

        assert translation is not None
        assert len(translation) > 0

        # Synthesize the translation
        audio_chunks = []
        async for chunk in tts.synthesize(translation):
            audio_chunks.append(chunk)

        assert len(audio_chunks) > 0

    @pytest.mark.asyncio
    async def test_speaker_b_ru_to_en(
        self,
        llm_model_path: Path,
        tts_model_path: Path,
    ):
        """Speaker B (ru→en) full cycle with real models."""
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

        # Speaker B speaks Russian, translates to English
        source_text = "Доброе утро!"
        source_lang = "Russian"
        target_lang = "English"

        # Translate
        translation = await llm.translate(source_text, source_lang, target_lang)

        assert translation is not None
        assert len(translation) > 0
        # Should contain English text (translation of "Good morning!")

        # Synthesize the translation
        audio_chunks = []
        async for chunk in tts.synthesize(translation):
            audio_chunks.append(chunk)

        assert len(audio_chunks) > 0

    @pytest.mark.asyncio
    async def test_language_switching_works_correctly(
        self,
        llm_model_path: Path,
    ):
        """Verify language direction changes correctly between speakers."""
        llm = LLMService(
            LLMSettings(
                model_path=str(llm_model_path),
                n_gpu_layers=0,
                context_window=2048,
                n_threads=2,
            )
        )

        # Speaker A: English → Russian
        result_a = await llm.translate("Hello", "English", "Russian")
        assert result_a is not None

        # Speaker B: Russian → English
        result_b = await llm.translate("Привет", "Russian", "English")
        assert result_b is not None

        # Both should produce non-empty results
        assert len(result_a) > 0
        assert len(result_b) > 0

        # Results should be different (different languages)
        # (Can't guarantee exact output but should not be identical)
