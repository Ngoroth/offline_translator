import asyncio
import argparse
from collections.abc import Sequence
from pathlib import Path
from typing import cast

import yaml

from loguru import logger

from app.core.audio import AudioPlayer, AudioRecorder
from app.core.audio.devices import (
    get_default_input_device,
    get_default_output_device,
    list_audio_devices,
    resolve_device,
)
from app.core.audio.recorder import AudioDeviceError
from app.core.audio.recorder_selector import select_recorder_factory
from app.core.config import AppSettings, load_settings
from app.core.input import BaseInput, EvdevInput, GPIOInput, KeyboardInput, Role
from app.core.logging import setup_logging
from app.core.startup import StartupVerifier
from app.services.stt import STTService
from app.services.llm import LLMService
from app.services.tts import TTSService
from app.orchestrator.pipeline import TranslationPipeline
from app.orchestrator.orchestrator import Orchestrator


def parse_cli_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        allow_abbrev=False,
        description="Run the offline translator application.",
    )
    _ = parser.add_argument(
        "--profile",
        metavar="NAME",
        help="Use profile NAME from config.yaml for this run.",
    )
    _ = parser.add_argument(
        "--playback-during-recording",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=("Allow translation playback before PTT release for this run (headset mode)."),
    )
    return parser.parse_args(argv)


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


async def main(
    profile_override: str | None = None,
    playback_during_recording_override: bool | None = None,
) -> int:
    # 1. Setup Logging (Must be first for diagnostics)
    setup_logging()
    logger.info("Starting Offline Translator...")

    try:
        # 2. Load Config
        settings = load_settings(profile_override=profile_override)
        if playback_during_recording_override is not None:
            settings.audio.playback_during_recording = playback_during_recording_override
        active_profile = profile_override or _get_current_profile_key()
        logger.info(f"Profile: {active_profile}")
        logger.info(f"Platform: {settings.platform} ({settings.input_mode})")

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
        recorder_factory = select_recorder_factory(settings.platform)
        recorder = cast(
            AudioRecorder,
            recorder_factory(
                sample_rate=settings.audio.sample_rate,
                device_index=input_device,
            ),
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
        return 0

    except KeyboardInterrupt:
        logger.info("Shutdown requested by user.")
        return 130
    except Exception as e:
        logger.exception(f"Fatal error during execution: {e}")
        return 1


def _get_current_profile_key(config_path: str | Path = "config.yaml") -> str:
    path = Path(config_path)
    if not path.exists():
        return "<unknown>"

    with open(path, "r", encoding="utf-8") as config_file:
        data = cast(object, yaml.safe_load(config_file))

    if not isinstance(data, dict):
        return "<unknown>"

    current_profile = data.get("current_profile")
    if isinstance(current_profile, str):
        return current_profile
    return "<unknown>"


def cli(argv: Sequence[str] | None = None) -> int:
    cli_args = parse_cli_args(argv)
    profile_override = getattr(cli_args, "profile", None)
    playback_during_recording_override = getattr(cli_args, "playback_during_recording", None)
    if profile_override is not None and not isinstance(profile_override, str):
        raise TypeError("Parsed CLI profile must be a string or None")
    if playback_during_recording_override is not None and not isinstance(
        playback_during_recording_override, bool
    ):
        raise TypeError("Parsed playback override must be a bool or None")
    if playback_during_recording_override is None:
        return asyncio.run(main(profile_override=profile_override))
    return asyncio.run(
        main(
            profile_override=profile_override,
            playback_during_recording_override=playback_during_recording_override,
        )
    )


if __name__ == "__main__":
    raise SystemExit(cli())
