import asyncio

from loguru import logger

from app.core.audio import AudioPlayer, AudioRecorder
from app.core.config import AppSettings, load_settings
from app.core.input import BaseInput, EvdevInput, GPIOInput, KeyboardInput, Role
from app.core.logging import setup_logging
from app.services.stt import STTService
from app.services.llm import LLMService
from app.services.tts import TTSService
from app.orchestrator.pipeline import TranslationPipeline
from app.orchestrator.orchestrator import Orchestrator


def get_input_handler(settings: AppSettings) -> BaseInput:
    """
    HAL Factory: Selects the appropriate input handler based on configuration.
    """
    # Use the new dual speaker keys from config
    key_map: dict[Role, str] = {
        "a": settings.speaker_a_key,
        "b": settings.speaker_b_key,
    }

    if settings.input_mode == "keyboard":
        return KeyboardInput(key_map=key_map)
    elif settings.input_mode == "evdev":
        return EvdevInput(
            device_path=settings.evdev.device,
            key_map=key_map,
        )
    elif settings.input_mode == "gpio":
        return GPIOInput(
            pin_map={"a": settings.gpio.pin_a, "b": settings.gpio.pin_b},
            chip_id=settings.gpio.chip_id,
            debounce_ms=settings.gpio.debounce_ms,
        )
    else:
        logger.error(f"Unsupported input mode: {settings.input_mode}. Defaulting to keyboard.")
        return KeyboardInput(key_map=key_map)


async def main():
    # 1. Setup Logging (Must be first for diagnostics)
    setup_logging()
    logger.info("Starting Offline Translator...")

    try:
        # 2. Load Config
        settings = load_settings()
        logger.info(f"Profile: {settings.platform} ({settings.input_mode})")

        # Log configuration (structured)
        logger.info("Configuration loaded", config=settings.model_dump(mode="json"))

        # 3. Initialize Hardware
        logger.info("Initializing hardware...")

        # Input via HAL Factory
        input_handler = get_input_handler(settings)
        input_handler.start()

        # Audio
        recorder = AudioRecorder(
            sample_rate=settings.audio.sample_rate, device_index=settings.audio.input_device_index
        )
        player = AudioPlayer(
            sample_rate=settings.audio.sample_rate, device_index=settings.audio.output_device_index
        )

        # 4. Initialize AI Services
        logger.info("Initializing AI Services...")

        # Collect TTS models
        tts_models: set[str] = set()
        if settings.tts.model_path:
            tts_models.add(settings.tts.model_path)

        # Add Dual Speaker voices (only if paths are configured)
        if settings.speaker_a_voice:
            tts_models.add(settings.speaker_a_voice)
        if settings.speaker_b_voice:
            tts_models.add(settings.speaker_b_voice)

        for speaker in settings.speakers.values():
            if speaker.tts_model:
                tts_models.add(speaker.tts_model)

        stt_service = STTService(settings.stt)
        llm_service = LLMService(settings.llm)
        tts_service = TTSService(settings.tts, extra_models=list(tts_models))

        # 5. Initialize Pipeline and Orchestrator
        logger.info("Initializing Orchestrator...")
        pipeline = TranslationPipeline(
            settings=settings,
            stt=stt_service,
            llm=llm_service,
            tts=tts_service,
            recorder=recorder,
            player=player,
        )

        orchestrator = Orchestrator(pipeline=pipeline, input_provider=input_handler)

        logger.info("System initialized. Ready for interaction. Ctrl+C to exit.")

        # 6. Run Orchestrator
        await orchestrator.run()

    except KeyboardInterrupt:
        logger.info("Shutdown requested by user.")
    except Exception as e:
        logger.exception(f"Fatal error during execution: {e}")


if __name__ == "__main__":
    asyncio.run(main())
