import asyncio
from asyncio import Task
import numpy as np
from loguru import logger

from app.core.config import AppSettings
from app.core.types import AudioPayload, TextPayload, TranslationPayload
from app.core.audio import AudioRecorder, AudioPlayer
from app.orchestrator.session import Session, SessionState
from app.services.stt import STTService
from app.services.llm import LLMService
from app.services.tts import TTSService


from typing import final


@final
class TranslationPipeline:
    def __init__(
        self,
        settings: AppSettings,
        stt: STTService,
        llm: LLMService,
        tts: TTSService,
        recorder: AudioRecorder,
        player: AudioPlayer,
    ):
        self.settings = settings
        self.stt = stt
        self.llm = llm
        self.tts = tts
        self.recorder = recorder
        self.player = player

        self.session: Session | None = None
        self.tasks: list[Task[None]] = []

        # Queues
        self.stt_queue: asyncio.Queue[AudioPayload | None] = asyncio.Queue()
        self.llm_queue: asyncio.Queue[TextPayload | None] = asyncio.Queue()
        self.tts_queue: asyncio.Queue[TranslationPayload | None] = asyncio.Queue()
        self.player_queue: asyncio.Queue[bytes | None] = asyncio.Queue()

    async def start_session(self, role: str = "a") -> Session:
        """
        Start a new translation session and worker tasks.

        Args:
            role: The speaker role ('a' or 'b') to determine languages.
        """
        if self.session and not self.session.cancel_event.is_set():
            await self.stop_session()

        self.session = Session()
        self.session.state = SessionState.LISTENING

        # Configure languages based on role
        if role in self.settings.speakers:
            speaker = self.settings.speakers[role]
            self.session.source_lang = speaker.from_lang
            self.session.target_lang = speaker.to_lang
            self.session.tts_model_path = speaker.tts_model
            logger.info(
                f"Session {self.session.session_id} started for Role {role}: {self.session.source_lang} -> {self.session.target_lang}"
            )
        else:
            logger.warning(
                f"Role {role} not found in settings.Using defaults: {self.session.source_lang} -> {self.session.target_lang}"
            )

        # Start Recorder
        self.recorder.start()

        # Start Workers
        self.tasks = [
            asyncio.create_task(self._stt_worker()),
            asyncio.create_task(self._llm_worker()),
            asyncio.create_task(self._tts_worker()),
            asyncio.create_task(self._player_worker()),
        ]

        return self.session

    async def stop_session(self) -> None:
        """Stop the current session and cancel workers."""
        if not self.session:
            return

        logger.info(f"Stopping session {self.session.session_id}")
        self.session.cancel_event.set()

        # Stop Recorder
        _ = self.recorder.stop()

        # Cancel tasks
        for task in self.tasks:
            _ = task.cancel()

        # Wait for tasks to finish (ignore CancelledError)
        if self.tasks:
            # We ignore the result of gather since we are cancelling everything
            _ = await asyncio.gather(*self.tasks, return_exceptions=True)

        self.tasks = []
        self._clear_queues()
        self.session = None

    def _clear_queues(self) -> None:
        """Drain all queues."""
        for q in [self.stt_queue, self.llm_queue, self.tts_queue, self.player_queue]:
            while not q.empty():
                try:
                    _ = q.get_nowait()
                except asyncio.QueueEmpty:
                    break

    async def handle_input_complete(self) -> None:
        """
        Called when PTT is released.
        Stops recording, retrieves audio, and feeds it into the pipeline.
        Then initiates graceful shutdown of workers via sentinels.
        """
        if not self.session:
            return

        logger.info("Input complete (PTT Released). Processing...")
        self.session.state = SessionState.PROCESSING

        # Stop Recorder and get audio
        # Note: recorder.stop() returns the buffer
        audio_data = self.recorder.stop()

        if len(audio_data) > 0:
            # Create payload
            payload: AudioPayload = {"audio": audio_data, "sample_rate": self.recorder.sample_rate}
            await self.stt_queue.put(payload)
        else:
            logger.warning("No audio recorded.")

        # Send sentinel to STT worker to signal end of stream
        await self.stt_queue.put(None)

    async def wait_for_completion(self) -> None:
        """Wait for all worker tasks to finish processing."""
        if not self.tasks:
            return

        # Wait for all tasks to complete (they should exit when they see sentinels)
        # We shield from cancellation just in case, but usually we just await
        try:
            _ = await asyncio.gather(*self.tasks)
        except Exception as e:
            logger.error(f"Error waiting for completion: {e}")

        self.tasks = []
        self.session = None  # Session over

    async def _stt_worker(self) -> None:
        """Consume audio, transcribe, push text."""
        if not self.session:
            return

        logger.debug("STT Worker started")
        try:
            while not self.session.cancel_event.is_set():
                payload = await self.stt_queue.get()

                # Sentinel handling
                if payload is None:
                    # Pass sentinel to next stage
                    await self.llm_queue.put(None)
                    break

                if self.session.state == SessionState.LISTENING:
                    self.session.state = SessionState.PROCESSING

                try:
                    text = await self.stt.transcribe(payload["audio"])
                    if text:
                        logger.debug(f"Transcribed: {text}")
                        await self.llm_queue.put(
                            {"text": text, "language": self.session.source_lang}
                        )
                except Exception as e:
                    logger.error(f"STT Error: {e}")

        except asyncio.CancelledError:
            logger.debug("STT Worker cancelled")

    async def _llm_worker(self) -> None:
        """Consume text, translate, push translation."""
        if not self.session:
            return

        logger.debug("LLM Worker started")
        try:
            while not self.session.cancel_event.is_set():
                payload = await self.llm_queue.get()

                if payload is None:
                    await self.tts_queue.put(None)
                    break

                try:
                    source_lang = self.session.source_lang
                    target_lang = self.session.target_lang

                    translated_text = await self.llm.translate(
                        payload["text"], source_lang, target_lang
                    )

                    if translated_text:
                        logger.debug(f"Translated: {translated_text}")
                        await self.tts_queue.put(
                            {
                                "text": translated_text,
                                "source_lang": source_lang,
                                "target_lang": target_lang,
                            }
                        )
                except Exception as e:
                    logger.error(f"LLM Error: {e}")

        except asyncio.CancelledError:
            logger.debug("LLM Worker cancelled")

    async def _tts_worker(self) -> None:
        """Consume translation, synthesize, push audio chunks."""
        if not self.session:
            return

        logger.debug("TTS Worker started")
        try:
            while not self.session.cancel_event.is_set():
                payload = await self.tts_queue.get()

                if payload is None:
                    await self.player_queue.put(None)
                    break

                try:
                    # Stream audio chunks
                    model_path = self.session.tts_model_path
                    async for chunk in self.tts.synthesize(payload["text"], model_path=model_path):
                        if self.session.cancel_event.is_set():
                            break
                        await self.player_queue.put(chunk)
                except Exception as e:
                    logger.error(f"TTS Error: {e}")

        except asyncio.CancelledError:
            logger.debug("TTS Worker cancelled")

    async def _player_worker(self) -> None:
        """Consume audio chunks, play them."""
        if not self.session:
            return

        logger.debug("Player Worker started")
        try:
            while not self.session.cancel_event.is_set():
                chunk = await self.player_queue.get()

                if chunk is None:
                    break

                if self.session.state != SessionState.SPEAKING:
                    self.session.state = SessionState.SPEAKING

                try:
                    data = np.frombuffer(chunk, dtype=np.float32)
                    await asyncio.to_thread(self.player.play, data)
                except Exception as e:
                    logger.error(f"Player Error: {e}")

        except asyncio.CancelledError:
            logger.debug("Player Worker cancelled")
