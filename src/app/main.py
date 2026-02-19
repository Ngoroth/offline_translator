import asyncio

from loguru import logger

from app.core.audio import AudioPlayer, AudioRecorder
from app.core.audio.devices import (
    get_default_input_device,
    get_default_output_device,
    list_audio_devices,
    resolve_device,
)
from app.core.audio.recorder import AudioDeviceError
from app.core.config import AppSettings, load_settings
from app.core.input import BaseInput, EvdevInput, GPIOInput, KeyboardInput, Role
from app.core.logging import setup_logging
from app.core.startup import StartupVerifier
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
    # Convert keys to str for keyboard/evdev inputs
    key_map_str: dict[Role, str] = {
        "a": str(settings.speaker_a_key),
        "b": str(settings.speaker_b_key),
    }

    if settings.input_mode == "keyboard":
        return KeyboardInput(key_map=key_map_str)
    elif settings.input_mode == "evdev":
        device_path = settings.evdev.device_path
        if device_path is None:
            raise ValueError("evdev.device_path must be configured when using evdev input mode")
        return EvdevInput(
            device_path=device_path,
            key_map=key_map_str,
        )
    elif settings.input_mode == "gpio":
        return GPIOInput(
            pin_map={"a": settings.gpio.pin_a, "b": settings.gpio.pin_b},
            chip_id=settings.gpio.chip_id,
            debounce_ms=settings.gpio.debounce_ms,
        )
    else:
        logger.error(f"Unsupported input mode: {settings.input_mode}. Defaulting to keyboard.")
        return KeyboardInput(key_map=key_map_str)


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

        # 2.1. Verify startup prerequisites
        verifier = StartupVerifier(settings)
        _ = verifier.verify_all()
        logger.info("Startup verification passed")

        # 2.5. Validate and resolve audio devices
        logger.info("Validating audio devices...")

        devices = list_audio_devices()
        logger.info(f"Found {len(devices)} audio devices")
        for dev in devices:
            logger.debug(f"  [{dev.index}] {dev.name} (in={dev.is_input}, out={dev.is_output})")

        input_device = resolve_device(
            settings.audio.input_device or settings.audio.input_device_index,
            is_input=True,
        )
        if input_device is None:
            default_input = get_default_input_device()
            if default_input is None:
                raise AudioDeviceError(
                    message="No input audio device available",
                    device=None,
                    suggestion="Connect a microphone and restart the application",
                )
            input_device = default_input.index
        logger.info(f"Input device resolved: {input_device}")

        output_device = resolve_device(
            settings.audio.output_device or settings.audio.output_device_index,
            is_input=False,
        )
        if output_device is None:
            default_output = get_default_output_device()
            if default_output is None:
                raise AudioDeviceError(
                    message="No output audio device available",
                    device=None,
                    suggestion="Connect speakers/headphones and restart the application",
                )
            output_device = default_output.index
        logger.info(f"Output device resolved: {output_device}")

        # 3. Initialize Hardware
        logger.info("Initializing hardware...")

        # Input via HAL Factory
        input_handler = get_input_handler(settings)
        input_handler.start()

        # Audio
        recorder = AudioRecorder(
            sample_rate=settings.audio.sample_rate,
            device_index=input_device,
        )
        player = AudioPlayer(
            sample_rate=settings.audio.sample_rate,
            device_index=output_device,
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
