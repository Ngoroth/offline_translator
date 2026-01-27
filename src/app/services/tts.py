import asyncio
import logging
import numpy as np
from pathlib import Path
from collections.abc import AsyncGenerator, Iterator
from typing import Protocol, cast, TYPE_CHECKING

from app.core.config import TTSSettings

if TYPE_CHECKING:
    from app.orchestrator.session import SessionManager

try:
    from piper.voice import PiperVoice
    from piper.config import SynthesisConfig
except ImportError:
    PiperVoice = None
    SynthesisConfig = None

logger = logging.getLogger(__name__)


class PiperConfigProto(Protocol):
    sample_rate: int


class SynthesisConfigProto(Protocol):
    speaker_id: int | None


class PiperAudioChunkProto(Protocol):
    audio_int16_bytes: bytes


class PiperVoiceProto(Protocol):
    config: PiperConfigProto

    def synthesize(
        self, text: str, syn_config: SynthesisConfigProto | None = None
    ) -> Iterator[PiperAudioChunkProto]: ...


class TTSService:
    # Remove obscured declarations that were causing redeclaration warnings
    voices: dict[str, PiperVoiceProto]
    # default_voice will be set in __init__
    # settings will be set in __init__
    # model_rate will be set in __init__
    # target_rate will be set in __init__
    # resample_needed will be set in __init__
    # resample_step will be set in __init__

    def __init__(
        self,
        settings: TTSSettings,
        extra_models: list[str] | None = None,
        session_manager: "SessionManager | None" = None,
    ):
        if PiperVoice is None or SynthesisConfig is None:
            raise ImportError("piper-tts is not installed")

        self.settings: TTSSettings = settings
        self.session_manager: "SessionManager | None" = session_manager
        self.voices = {}

        # Collect all models to load
        models_to_load: set[str] = set()
        if settings.model_path:
            models_to_load.add(settings.model_path)
        if extra_models:
            models_to_load.update(extra_models)

        for model_path_str in models_to_load:
            self._load_voice(model_path_str)

        # Set default voice (first one or from settings)
        self.default_voice: PiperVoiceProto
        if settings.model_path in self.voices:
            self.default_voice = self.voices[settings.model_path]
        elif self.voices:
            self.default_voice = next(iter(self.voices.values()))
        else:
            raise ValueError("No TTS models loaded")

        # Resampling setup (using default voice config for now, assuming similar rates)
        # TODO: Handle per-voice sample rates if they differ
        self.model_rate: int = self.default_voice.config.sample_rate
        self.target_rate: int = 16000
        self.resample_needed: bool = self.model_rate != self.target_rate
        self.resample_step: float = self.model_rate / self.target_rate

    def _load_voice(self, model_path_str: str) -> None:
        path = Path(model_path_str)
        if not path.exists():
            logger.warning(f"TTS Model not found: {path}")
            return

        config_path = path.with_suffix(path.suffix + ".json")
        if not config_path.exists():
            config_path = path.parent / (path.stem + ".onnx.json")

        c_path = str(config_path) if config_path.exists() else None

        try:
            # We must verify PiperVoice is not None before calling load
            if PiperVoice is None:
                raise ImportError("piper-tts is not installed")

            voice = cast(
                PiperVoiceProto, cast(object, PiperVoice.load(str(path), config_path=c_path))
            )
            self.voices[model_path_str] = voice
            logger.info(f"Loaded TTS model: {model_path_str}")
        except Exception as e:
            logger.error(f"Failed to load TTS model {model_path_str}: {e}")

    async def synthesize(
        self,
        text: str,
        speaker_id: int | None = None,
        model_path: str | None = None,
        session_id: str | None = None,
    ) -> AsyncGenerator[bytes, None]:
        """
        Synthesize text and yield float32 audio bytes at 16kHz.

        Args:
            text: Text to synthesize
            speaker_id: Optional speaker ID for multi-speaker models.
            model_path: specific model to use.
            session_id: Optional session ID for cancellation checks.
        """
        if session_id and self.session_manager and not self.session_manager.is_valid(session_id):
            return

        queue: asyncio.Queue[bytes | None] = asyncio.Queue()
        loop = asyncio.get_running_loop()

        # Resolve voice
        voice = self.default_voice
        if model_path and model_path in self.voices:
            voice = self.voices[model_path]
        elif model_path:
            logger.warning(f"Requested model {model_path} not loaded. Using default.")

        # Resolve speaker ID
        sid = speaker_id if speaker_id is not None else self.settings.speaker_id

        # Update resampling step if voice differs (optimization: do check inside producer?)
        # For MVP we assume all models have same sample rate or we re-calc.
        # Let's re-calc inside producer to be safe or just use the voice's config.
        model_rate = voice.config.sample_rate
        resample_needed = model_rate != self.target_rate
        resample_step = model_rate / self.target_rate

        def producer() -> None:
            next_input_index: float = 0.0
            last_sample: float | None = None

            try:
                # We know SynthesisConfig is not None here because of __init__ check
                if SynthesisConfig is not None:
                    if (
                        session_id
                        and self.session_manager
                        and not self.session_manager.is_valid(session_id)
                    ):
                        _ = loop.call_soon_threadsafe(queue.put_nowait, None)
                        return

                    syn_config = SynthesisConfig(speaker_id=sid)
                    stream = voice.synthesize(text, syn_config=syn_config)

                    for chunk in stream:
                        if (
                            session_id
                            and self.session_manager
                            and not self.session_manager.is_valid(session_id)
                        ):
                            break

                        # PROCESS CHUNK IN THREAD (CPU Bound)

                        chunk_bytes = chunk.audio_int16_bytes
                        int16_data = np.frombuffer(chunk_bytes, dtype=np.int16)
                        float_data = int16_data.astype(np.float32) / 32768.0

                        output_bytes = b""

                        if not resample_needed:
                            output_bytes = float_data.tobytes()
                        else:
                            # ... resampling logic ...
                            n_in = len(float_data)
                            if n_in == 0:
                                continue

                            if last_sample is not None:
                                full_data = np.concatenate(
                                    (np.array([last_sample], dtype=np.float32), float_data)
                                )
                                xp = np.arange(-1, n_in)
                            else:
                                full_data = float_data
                                xp = np.arange(0, n_in)

                            limit = n_in
                            if limit <= next_input_index:
                                next_input_index -= float(n_in)
                                if len(float_data) > 0:
                                    last_sample = float(cast(float, float_data[-1]))
                                continue

                            num_samples = int((limit - next_input_index) / resample_step)

                            if num_samples > 0:
                                out_indices = (
                                    next_input_index + np.arange(num_samples) * resample_step
                                )
                                output = np.interp(out_indices, xp, full_data)
                                output_bytes = output.astype(np.float32).tobytes()

                                next_input_index = float(
                                    (cast(float, out_indices[-1]) + resample_step) - float(n_in)
                                )
                            else:
                                next_input_index -= float(n_in)

                            if len(float_data) > 0:
                                last_sample = float(cast(float, float_data[-1]))

                        if output_bytes:
                            _ = loop.call_soon_threadsafe(queue.put_nowait, output_bytes)

                _ = loop.call_soon_threadsafe(queue.put_nowait, None)  # Sentinel
            except Exception as e:
                logger.error(f"TTS Synthesis error: {e}")
                _ = loop.call_soon_threadsafe(queue.put_nowait, None)

        # Start producer in thread
        _ = asyncio.create_task(asyncio.to_thread(producer))

        while True:
            chunk_bytes = await queue.get()
            if chunk_bytes is None:
                break
            yield chunk_bytes
