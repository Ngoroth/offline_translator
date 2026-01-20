import asyncio
import sys
from pathlib import Path
from loguru import logger

from app.settings import load_settings
from app.core.output_console import ConsoleOutput
from app.core.input_windows import KeyboardInput
from app.core.audio import AudioRecorder, AudioPlayer
from app.services.stt import STTService
from app.services.translator import TranslatorService
from app.services.tts import TTSService
from app.utils.vad import VADService, SilenceDetector


class Orchestrator:
    def __init__(self):
        self.settings = load_settings()
        self.output = ConsoleOutput()

        # Queues (now passing dictionaries with 'role' and 'data')
        self.stt_queue = asyncio.Queue()
        self.llm_queue = asyncio.Queue()
        self.tts_queue = asyncio.Queue()
        self.playback_queue = asyncio.Queue()

        # State
        self.is_recording = False
        self.interrupt_event = asyncio.Event()
        self.playback_allowed = asyncio.Event()
        self.playback_allowed.set()  # Allowed by default
        self.current_session = 0

    def clear_queues(self):
        for q in [self.stt_queue, self.llm_queue, self.tts_queue, self.playback_queue]:
            while not q.empty():
                try:
                    q.get_nowait()
                    q.task_done()
                except (asyncio.QueueEmpty, ValueError):
                    break

    async def audio_capture_task(self, recorder, input_handler, player):
        vad = VADService(sample_rate=self.settings.audio.sample_rate)
        silence_detector = SilenceDetector(sample_rate=self.settings.audio.sample_rate)

        while True:
            # wait_for_press now returns 'a' or 'b'
            role = await asyncio.to_thread(input_handler.wait_for_press)

            self.current_session += 1
            session_id = self.current_session

            self.is_recording = True
            self.interrupt_event.set()  # Signal interruption to playback
            self.playback_allowed.clear()  # Block playback while recording
            player.stop()  # Immediately stop current playback
            self.clear_queues()

            self.output.status(f"Recording ({role})...")
            recorder.start()
            silence_detector.reset()
            speech_in_segment = False

            # 30ms frames for VAD
            frame_samples = int(self.settings.audio.sample_rate * 0.03)

            while input_handler.is_pressed(role):
                await asyncio.sleep(0.03)
                if session_id != self.current_session:
                    break  # Interrupted by another press?

                # Check VAD
                chunk = recorder.get_last_chunk(frame_samples)
                if len(chunk) == frame_samples:
                    is_speech = vad.is_speech(chunk)
                    if is_speech:
                        speech_in_segment = True

                    if silence_detector.is_silent_timeout(is_speech, frame_samples):
                        # Silence detected: Extract what we have and send it to STT ONLY if speech was heard
                        mid_audio = recorder.extract_buffer()
                        if speech_in_segment and len(mid_audio) > 1600:
                            self.output.status("Pause detected, processing segment...")
                            await self.stt_queue.put(
                                {"role": role, "audio": mid_audio, "session_id": session_id}
                            )
                        silence_detector.reset()
                        speech_in_segment = False
                        # Do NOT break, continue listening until button is released

            # Final audio data (after button release or interruption)
            audio_data = recorder.stop()
            self.is_recording = False
            self.interrupt_event.clear()

            if session_id != self.current_session:
                continue

            # Start processing immediately ONLY if speech was heard in the last segment
            if speech_in_segment and len(audio_data) > 1600:
                await self.stt_queue.put(
                    {"role": role, "audio": audio_data, "session_id": session_id}
                )
            elif not speech_in_segment:
                self.output.status("No speech detected in last segment.")
            else:
                self.output.status("Too short, ignored.")

            # Wait for physical button release before allowing playback (unless in streaming mode)
            if not self.settings.audio.playback_during_recording:
                while input_handler.is_pressed(role):
                    await asyncio.sleep(0.05)
                    if session_id != self.current_session:
                        break

            self.playback_allowed.set()  # Allow playback after button release

    async def stt_worker(self, stt_service):
        # Mapping for human-readable names to ISO codes
        lang_map = {
            "english": "en",
            "russian": "ru",
            "spanish": "es",
            "french": "fr",
            "german": "de",
            # Add more as needed or move to settings
        }

        while True:
            payload = await self.stt_queue.get()
            session_id = payload["session_id"]
            role = payload["role"]
            audio_data = payload["audio"]

            if session_id != self.current_session:
                self.stt_queue.task_done()
                continue

            speaker_cfg = self.settings.speakers.get(role)
            target_lang_code = None
            if speaker_cfg:
                target_lang_code = lang_map.get(speaker_cfg.from_lang.lower())

            self.output.status(f"Transcribing ({role}, lang={target_lang_code or 'auto'})...")
            try:
                # Use role-specific language for STT to avoid mis-detection
                text = await asyncio.to_thread(
                    stt_service.transcribe, audio_data, language=target_lang_code
                )

                if session_id != self.current_session:
                    continue

                if text.strip():
                    self.output.status(f"[{role}] Heard: {text}")
                    await self.llm_queue.put({"role": role, "text": text, "session_id": session_id})
                else:
                    self.output.status("Nothing heard.")
            except Exception as e:
                logger.error(f"STT Error: {e}")
            finally:
                self.stt_queue.task_done()

    async def llm_worker(self, translator_service):
        while True:
            payload = await self.llm_queue.get()
            session_id = payload["session_id"]
            role = payload["role"]
            text = payload["text"]

            if session_id != self.current_session:
                self.llm_queue.task_done()
                continue

            speaker_cfg = self.settings.speakers.get(role)
            if not speaker_cfg:
                logger.error(f"No config for speaker {role}")
                self.llm_queue.task_done()
                continue

            self.output.status(f"Translating ({role})...")
            try:
                sentence_buffer = ""
                async for token in translator_service.translate_stream(
                    text, speaker_cfg.from_lang, speaker_cfg.to_lang
                ):
                    if session_id != self.current_session:
                        break

                    sentence_buffer += token
                    if any(c in token for c in ".!?"):
                        await self.tts_queue.put(
                            {
                                "role": role,
                                "text": sentence_buffer.strip(),
                                "session_id": session_id,
                            }
                        )
                        sentence_buffer = ""

                if session_id == self.current_session and sentence_buffer.strip():
                    await self.tts_queue.put(
                        {"role": role, "text": sentence_buffer.strip(), "session_id": session_id}
                    )
            except Exception as e:
                logger.error(f"LLM Error: {e}")
            finally:
                self.llm_queue.task_done()

    async def tts_worker(self, tts_services):
        while True:
            payload = await self.tts_queue.get()
            session_id = payload["session_id"]
            role = payload["role"]
            sentence = payload["text"]

            if session_id != self.current_session:
                self.tts_queue.task_done()
                continue

            self.output.status(f"Synthesizing ({role}): {sentence[:20]}...")
            try:
                # Select service based on speaker's tts_model
                service = tts_services.get(role, tts_services.get("default"))
                if not service:
                    logger.error("No TTS service available")
                    continue

                for audio_chunk in service.synthesize_stream(sentence):
                    if session_id != self.current_session:
                        break
                    await self.playback_queue.put({"audio": audio_chunk, "session_id": session_id})
            except Exception as e:
                logger.error(f"TTS Error: {e}")
            finally:
                self.tts_queue.task_done()

    async def playback_worker(self, player):
        while True:
            payload = await self.playback_queue.get()
            session_id = payload["session_id"]
            audio_chunk = payload["audio"]

            if session_id != self.current_session:
                self.playback_queue.task_done()
                continue

            # If we don't allow playback during recording, wait for permission
            if not self.settings.audio.playback_during_recording:
                await self.playback_allowed.wait()

            if session_id != self.current_session or self.interrupt_event.is_set():
                # Playback interrupted, wait for next clean state
                self.playback_queue.task_done()
                continue

            try:
                await asyncio.to_thread(player.play, audio_chunk)
            except Exception as e:
                logger.error(f"Playback Error: {e}")
            finally:
                self.playback_queue.task_done()

    async def run(self):
        self.output.status("Initializing services...")

        # Initialize Hardware
        key_map = {"a": self.settings.input.ptt_a, "b": self.settings.input.ptt_b}
        input_handler = KeyboardInput(key_map=key_map)
        recorder = AudioRecorder(
            sample_rate=self.settings.audio.sample_rate,
            device_index=self.settings.audio.input_device_index,
        )
        player = AudioPlayer(
            sample_rate=self.settings.audio.sample_rate,
            device_index=self.settings.audio.output_device_index,
        )

        # Initialize AI
        stt = STTService(model_path=self.settings.stt.model_path)
        translator = TranslatorService(
            model_path=self.settings.llm.model_path,
            n_ctx=self.settings.llm.n_ctx,
            thread_count=self.settings.llm.thread_count,
        )

        # Initialize TTS services (one per speaker if models differ)
        tts_services = {}
        default_tts = TTSService(model_path=self.settings.tts.model_path)
        tts_services["default"] = default_tts

        for role, speaker in self.settings.speakers.items():
            if speaker.tts_model and speaker.tts_model != self.settings.tts.model_path:
                model_path = Path(speaker.tts_model)
                if model_path.exists():
                    self.output.status(f"Loading TTS for {role}: {speaker.tts_model}")
                    try:
                        tts_services[role] = TTSService(model_path=speaker.tts_model)
                    except Exception as e:
                        logger.error(
                            f"Failed to load specific TTS for {role}: {e}. Falling back to default."
                        )
                        tts_services[role] = default_tts
                else:
                    logger.warning(
                        f"TTS model {speaker.tts_model} not found. Falling back to default."
                    )
                    tts_services[role] = default_tts
            else:
                tts_services[role] = default_tts

        self.output.status("Ready! Press Space (A) or Alt (B).")

        # Start Tasks
        await asyncio.gather(
            self.audio_capture_task(recorder, input_handler, player),
            self.stt_worker(stt),
            self.llm_worker(translator),
            self.tts_worker(tts_services),
            self.playback_worker(player),
        )


def main():
    logger.add("logs/app.log", rotation="10 MB")
    orchestrator = Orchestrator()
    try:
        asyncio.run(orchestrator.run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
