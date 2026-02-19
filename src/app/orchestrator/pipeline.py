import asyncio
from asyncio import Task
import numpy as np
from loguru import logger

from app.core.config import AppSettings
from app.core.types import AudioPayload, TextPayload, TranslationPayload
from app.core.audio import AudioRecorder, AudioPlayer
from app.orchestrator.session import Session, SessionState, SessionManager
from app.services.stt import STTService
from app.services.llm import LLMService
from app.services.tts import TTSService
from app.utils.vad import VADService, SilenceDetector


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

        self.session_manager = SessionManager()

        # Inject session manager into services for cooperative cancellation
        self.stt.session_manager = self.session_manager
        self.llm.session_manager = self.session_manager
        self.tts.session_manager = self.session_manager

        self.session: Session | None = None
        self.tasks: list[Task[None]] = []
        self.vad_task: Task[None] | None = None

        # VAD Components
        self.vad_service = VADService(
            aggressiveness=settings.vad.aggressiveness,
            sample_rate=settings.audio.sample_rate,
        )
        self.silence_detector = SilenceDetector(
            threshold_ms=settings.vad.threshold_ms,
            sample_rate=settings.audio.sample_rate,
        )
        self.vad_auto_harvest = settings.vad.auto_harvest

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

        # Determine configuration based on role
        source_lang = self.settings.speaker_a_lang  # Default to role A
        target_lang = self.settings.speaker_b_lang
        tts_voice: str | None = None

        if role == "a":
            source_lang = self.settings.speaker_a_lang
            target_lang = self.settings.speaker_b_lang
            # TTS voice should match the TARGET language (what we're translating TO)
            # For speaker A (EN->RU), we need Russian TTS
            tts_voice = self.settings.speaker_b_voice
            if not tts_voice and "a" in self.settings.speakers:
                tts_voice = self.settings.speakers["a"].tts_model
        elif role == "b":
            source_lang = self.settings.speaker_b_lang
            target_lang = self.settings.speaker_a_lang
            # TTS voice should match the TARGET language (what we're translating TO)
            # For speaker B (RU->EN), we need English TTS
            tts_voice = self.settings.speaker_a_voice
            if not tts_voice and "b" in self.settings.speakers:
                tts_voice = self.settings.speakers["b"].tts_model
        elif role in self.settings.speakers:
            # Fallback for other roles if defined in legacy speakers dict
            speaker = self.settings.speakers[role]
            source_lang = speaker.from_lang
            target_lang = speaker.to_lang
            tts_voice = speaker.tts_model

        # Start session via manager (returns configured Session object)
        self.session = self.session_manager.start_session(
            source_lang=source_lang,
            target_lang=target_lang,
            tts_voice=tts_voice,
        )
        self.session.state = SessionState.LISTENING

        logger.info(
            f"Session {self.session.session_id} started for Role {role}: "
            + f"{self.session.source_lang} -> {self.session.target_lang} "
            + f"(Voice: {self.session.tts_voice})"
        )

        # Start Recorder
        self.recorder.start()

        # Start VAD Worker
        self.vad_task = asyncio.create_task(self._vad_worker())

        # Start Workers
        self.tasks = [
            asyncio.create_task(self._stt_worker()),
            asyncio.create_task(self._llm_worker()),
            asyncio.create_task(self._tts_worker()),
            asyncio.create_task(self._player_worker()),
        ]

        return self.session

    async def handle_barge_in(self) -> None:
        """
        Handle barge-in interruption.
        Stops current playback/processing immediately, clears queues, and prepares for new input.
        """
        if not self.session:
            return

        logger.info(f"Barge-in detected: Cancelling session {self.session.session_id}")
        await self.stop_session()
        # State will be set to LISTENING by next start_session call

    async def stop_session(self) -> None:
        """Stop the current session and cancel workers."""
        if not self.session:
            return

        logger.info(f"Stopping session {self.session.session_id}")
        self.session.cancel_event.set()
        self.session_manager.cancel_session(self.session.session_id)

        # Stop Player immediately to clear hardware buffer
        await asyncio.to_thread(self.player.stop)

        # Stop Recorder
        _ = self.recorder.stop()

        # Cancel VAD task
        if self.vad_task:
            _ = self.vad_task.cancel()
            self.vad_task = None

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

        # Stop VAD worker first to avoid race on buffer extraction
        if self.vad_task:
            _ = self.vad_task.cancel()
            try:
                await self.vad_task
            except asyncio.CancelledError:
                pass
            self.vad_task = None

        # Stop Recorder and get audio
        # Note: recorder.stop() returns the buffer
        audio_data = self.recorder.stop()

        if len(audio_data) > 0:
            # Create payload
            payload: AudioPayload = {
                "audio": audio_data,
                "sample_rate": self.recorder.sample_rate,
                "session_id": self.session.session_id,
            }
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

    async def _vad_worker(self) -> None:
        """
        Continuously monitor audio stream for speech/silence.
        Harvests audio segments when silence threshold is reached.
        """
        if not self.session:
            return

        logger.debug("VAD Worker started")
        self.silence_detector.reset()

        try:
            while not self.session.cancel_event.is_set():
                # Get chunk from recorder (non-blocking if possible, but get_chunk is async)
                try:
                    # Timeout to check cancel event periodically if no audio
                    chunk = await asyncio.wait_for(self.recorder.get_chunk(), timeout=0.1)
                except asyncio.TimeoutError:
                    continue

                # Note: We no longer check session.state here because we want to
                # continue harvesting segments even while previous ones are processing.
                # The session.state check was blocking multi-segment harvesting (FR11).
                # VAD should run as long as we're recording, regardless of processing state.

                # Run VAD
                # chunk is float32
                is_speech = self.vad_service.is_speech(chunk)

                # Check silence
                if self.silence_detector.is_silent_timeout(is_speech, len(chunk)):
                    if self.vad_auto_harvest:
                        logger.info("VAD: Silence threshold reached. Harvesting segment.")

                        # Extract whatever is in the recorder buffer
                        # This clears the buffer, so we get the "sentence" so far.
                        audio_data = self.recorder.extract_buffer()

                        if len(audio_data) > 0:
                            payload: AudioPayload = {
                                "audio": audio_data,
                                "sample_rate": self.recorder.sample_rate,
                                "session_id": self.session.session_id,
                            }
                            await self.stt_queue.put(payload)
                            logger.debug(f"Pushed {len(audio_data)} samples to STT queue")

                        # Reset silence detector
                        self.silence_detector.reset()
                    else:
                        # In PTT-only mode, just reset the detector but keep recording
                        logger.debug(
                            "VAD: Silence detected, but waiting for PTT release (auto_harvest=False)"
                        )
                        self.silence_detector.reset()

        except asyncio.CancelledError:
            logger.debug("VAD Worker cancelled")

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

                # Note: We no longer transition to PROCESSING here because it was
                # blocking VAD from collecting additional segments during multi-phrase
                # sessions. The state transition is now handled in handle_input_complete()
                # when the user releases PTT. This fixes FR11 (10 phrases per hold session).

                try:
                    session_id = payload["session_id"]
                    # Pass source language to STT to optimize decoding
                    text = await self.stt.transcribe(
                        payload["audio"],
                        language=self.session.source_lang,
                        session_id=session_id,
                    )
                    if text:
                        logger.info(f"STT Transcribed: {text}")

                        llm_payload: TextPayload = {
                            "text": text,
                            "language": self.session.source_lang,
                            "session_id": session_id,
                        }
                        logger.debug(f"Sending to LLM queue: {llm_payload}")
                        await self.llm_queue.put(llm_payload)
                        logger.debug("Sent to LLM queue successfully")
                except Exception as e:
                    audio_data = payload.get("audio")
                    session_id = payload.get("session_id", "unknown")
                    logger.error(
                        f"STT Error [session={session_id}, audio_len={len(audio_data) if audio_data is not None else 0}]: {e}"
                    )

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
                    session_id = payload["session_id"]

                    logger.info(
                        f"LLM translating: '{payload['text']}' from {source_lang} to {target_lang}"
                    )

                    translated_text = await self.llm.translate(
                        payload["text"], source_lang, target_lang, session_id=session_id
                    )

                    if translated_text:
                        logger.info(f"LLM Translated: {translated_text}")
                        await self.tts_queue.put(
                            {
                                "text": translated_text,
                                "source_lang": source_lang,
                                "target_lang": target_lang,
                                "session_id": session_id,
                            }
                        )
                except Exception as e:
                    session_id = payload.get("session_id", "unknown")
                    source_lang = self.session.source_lang if self.session else "unknown"
                    target_lang = self.session.target_lang if self.session else "unknown"
                    logger.error(
                        f"LLM Error [session={session_id}, {source_lang}->{target_lang}]: {e}"
                    )

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
                    voice = self.session.tts_voice
                    session_id = payload["session_id"]
                    async for chunk in self.tts.synthesize(
                        payload["text"], model_path=voice, session_id=session_id
                    ):
                        if self.session.cancel_event.is_set():
                            break
                        await self.player_queue.put(chunk)
                except Exception as e:
                    session_id = payload.get("session_id", "unknown")
                    voice = self.session.tts_voice if self.session else "unknown"
                    logger.error(f"TTS Error [session={session_id}, voice={voice}]: {e}")

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
                    session_id = self.session.session_id if self.session else "unknown"
                    logger.error(f"Player Error [session={session_id}]: {e}")

        except asyncio.CancelledError:
            logger.debug("Player Worker cancelled")
