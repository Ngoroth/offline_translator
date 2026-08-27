import asyncio
import numpy as np
from faster_whisper import WhisperModel
from loguru import logger
from app.core.config import STTSettings
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.performance import PerformanceEventEmitter
    from app.orchestrator.session import SessionManager


class STTError(Exception):
    """Base exception for STT service errors."""

    pass


class STTModelLoadError(STTError):
    """Raised when the model fails to load."""

    pass


class STTTranscriptionError(STTError):
    """Raised when transcription fails."""

    pass


class STTService:
    """
    Speech-to-Text service using Faster-Whisper.
    """

    performance: "PerformanceEventEmitter | None"

    def __init__(
        self,
        settings: STTSettings,
        session_manager: "SessionManager | None" = None,
        performance: "PerformanceEventEmitter | None" = None,
    ):
        """
        Initialize the STT service with settings.
        Model is loaded lazily on first transcription or can be loaded explicitly.

        Args:
            settings: STT-specific settings.
            session_manager: Optional SessionManager for cancellation checks.
        """
        self.settings: STTSettings = settings
        self.session_manager: "SessionManager | None" = session_manager
        self.performance = performance
        self._model: WhisperModel | None = None
        self._lock: asyncio.Lock = asyncio.Lock()

    async def _get_model(self) -> WhisperModel:
        """
        Ensure the model is loaded and return it.
        Uses a lock to prevent multiple simultaneous initializations.
        """
        async with self._lock:
            if self._model is None:
                try:
                    logger.debug(
                        "Loading Faster-Whisper model: {} (device={}, compute_type={})",
                        self.settings.model_path,
                        self.settings.device,
                        self.settings.compute_type,
                    )
                    # WhisperModel initialization is blocking, offload to thread
                    self._model = await asyncio.to_thread(
                        WhisperModel,
                        self.settings.model_path,
                        device=self.settings.device,
                        compute_type=self.settings.compute_type,
                    )
                except Exception as e:
                    logger.error("Failed to load Faster-Whisper model: {}", e)
                    raise STTModelLoadError(
                        f"Failed to load model from {self.settings.model_path}"
                    ) from e
            return self._model

    async def warmup(self) -> None:
        """Load the model and run one full transcription to initialize inference.

        Moves the slow lazy model load and first-call graph initialization out
        of the critical path so the first real PTT cycle starts warm.
        Uses silence (not noise) so whisper terminates immediately instead of
        hallucinating indefinitely, and is wrapped in a timeout so warmup can
        never hang startup.
        """
        try:
            model = await self._get_model()
            samples = np.zeros(16000, dtype=np.float32)

            def _run_warmup() -> None:
                # Bypass the VAD filter so the decode graph is fully initialized.
                segments, _ = model.transcribe(samples, beam_size=1, vad_filter=False)
                for _segment in segments:
                    pass

            await asyncio.wait_for(asyncio.to_thread(_run_warmup), timeout=30)
            logger.info("STT warmup complete")
        except Exception as e:
            logger.warning("STT warmup failed (will load lazily on first use): {}", e)

    async def transcribe(
        self, audio: np.ndarray, language: str | None = None, session_id: str | None = None
    ) -> str | None:
        """
        Transcribe 16kHz mono float32 audio to text.

        Args:
            audio: Numpy array of audio samples.
            language: Target language code (e.g., "en", "ru"). If None, uses default.
            session_id: Optional session ID to check for cancellation.

        Returns:
            The gathered transcribed text, or None if cancelled.

        Raises:
            STTTranscriptionError: If transcription fails.
        """
        if session_id and self.session_manager and not self.session_manager.is_valid(session_id):
            logger.debug(f"STT: Pre-check cancelled for session {session_id}")
            return None

        model = await self._get_model()

        try:
            # Transcription is CPU/GPU intensive and blocking
            # model.transcribe returns (segments_generator, info)
            # Both the call and the iteration over segments are blocking

            def _run_transcription():
                segments, info = model.transcribe(
                    audio,
                    language=language or self.settings.language,
                    beam_size=self.settings.beam_size,
                    vad_filter=True,  # Secondary safeguard as per requirements
                )
                # Gathering segments into a list triggers the actual transcription
                return " ".join([segment.text for segment in segments]).strip(), info

            logger.debug("Starting transcription...")
            start_time = asyncio.get_event_loop().time()

            async with self._lock:
                # Check validity again after acquiring lock
                if (
                    session_id
                    and self.session_manager
                    and not self.session_manager.is_valid(session_id)
                ):
                    logger.debug(f"STT: Locked pre-check cancelled for session {session_id}")
                    return None

                if self.performance and session_id:
                    self.performance.emit(
                        session_id,
                        "stt_start",
                        audio_ms=round(len(audio) * 1000 / 16000),
                    )
                text, info = await asyncio.to_thread(_run_transcription)

            if (
                session_id
                and self.session_manager
                and not self.session_manager.is_valid(session_id)
            ):
                logger.debug(f"STT: Post-check cancelled for session {session_id}")
                return None

            duration = asyncio.get_event_loop().time() - start_time
            if self.performance and session_id:
                self.performance.emit(
                    session_id,
                    "stt_end",
                    audio_ms=round(len(audio) * 1000 / 16000),
                    output_chars=len(text),
                )
            logger.debug(
                "Transcription completed in {:.2f}s. Detected language: {} ({:.2f} probability)",
                duration,
                info.language,
                info.language_probability,
            )

            return text

        except Exception as e:
            logger.error("Transcription failed: {}", e)
            raise STTTranscriptionError("Failed to transcribe audio") from e
