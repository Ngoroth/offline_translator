import asyncio
import numpy as np
from faster_whisper import WhisperModel
from loguru import logger
from app.core.config import STTSettings


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

    def __init__(self, settings: STTSettings):
        """
        Initialize the STT service with settings.
        Model is loaded lazily on first transcription or can be loaded explicitly.

        Args:
            settings: STT-specific settings.
        """
        self.settings: STTSettings = settings
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

    async def transcribe(self, audio: np.ndarray) -> str:
        """
        Transcribe 16kHz mono float32 audio to text.

        Args:
            audio: Numpy array of audio samples.

        Returns:
            The gathered transcribed text.

        Raises:
            STTTranscriptionError: If transcription fails.
        """
        model = await self._get_model()

        try:
            # Transcription is CPU/GPU intensive and blocking
            # model.transcribe returns (segments_generator, info)
            # Both the call and the iteration over segments are blocking

            def _run_transcription():
                segments, info = model.transcribe(
                    audio,
                    language=self.settings.language,
                    beam_size=self.settings.beam_size,
                    vad_filter=True,  # Secondary safeguard as per requirements
                )
                # Gathering segments into a list triggers the actual transcription
                return " ".join([segment.text for segment in segments]).strip(), info

            logger.debug("Starting transcription...")
            start_time = asyncio.get_event_loop().time()

            text, info = await asyncio.to_thread(_run_transcription)

            duration = asyncio.get_event_loop().time() - start_time
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
