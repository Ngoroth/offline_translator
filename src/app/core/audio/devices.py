from dataclasses import dataclass
from typing import TYPE_CHECKING

import sounddevice as sd
from loguru import logger

if TYPE_CHECKING:
    from typings.sounddevice import DeviceInfo


@dataclass
class AudioDevice:
    index: int
    name: str
    is_input: bool
    is_output: bool
    is_default: bool
    sample_rate: int | None


def _parse_device(idx: int, dev: "DeviceInfo", is_default: bool) -> AudioDevice:
    return AudioDevice(
        index=idx,
        name=dev["name"],
        is_input=dev["max_input_channels"] > 0,
        is_output=dev["max_output_channels"] > 0,
        is_default=is_default,
        sample_rate=int(dev["default_samplerate"]) if dev["default_samplerate"] else None,
    )


def list_audio_devices() -> list[AudioDevice]:
    devices: list[AudioDevice] = []
    try:
        all_devices = sd.query_devices()
        default_input, default_output = sd.default.device

        for idx, dev in enumerate(all_devices):
            is_default = idx == default_input or idx == default_output
            devices.append(_parse_device(idx, dev, is_default))
    except Exception as e:
        logger.error(f"Failed to list audio devices: {e}")

    return devices


def get_default_input_device() -> AudioDevice | None:
    try:
        default_input, _ = sd.default.device
        if default_input is None or default_input < 0:
            devices = list_audio_devices()
            for dev in devices:
                if dev.is_input:
                    return dev
            return None

        all_devices = sd.query_devices()
        if default_input >= len(all_devices):
            return None

        dev = all_devices[default_input]
        return _parse_device(default_input, dev, is_default=True)
    except Exception as e:
        logger.error(f"Failed to get default input device: {e}")
        return None


def get_default_output_device() -> AudioDevice | None:
    try:
        _, default_output = sd.default.device
        if default_output is None or default_output < 0:
            devices = list_audio_devices()
            for dev in devices:
                if dev.is_output:
                    return dev
            return None

        all_devices = sd.query_devices()
        if default_output >= len(all_devices):
            return None

        dev = all_devices[default_output]
        return _parse_device(default_output, dev, is_default=True)
    except Exception as e:
        logger.error(f"Failed to get default output device: {e}")
        return None


def resolve_device(device_name: str | int | None, is_input: bool) -> int | str | None:
    if device_name is None:
        default_dev = get_default_input_device() if is_input else get_default_output_device()
        return default_dev.index if default_dev else None

    if isinstance(device_name, int):
        return device_name

    devices = list_audio_devices()
    device_name_lower = device_name.lower()

    for dev in devices:
        if dev.name.lower() == device_name_lower:
            if is_input and dev.is_input:
                return dev.index
            if not is_input and dev.is_output:
                return dev.index

    logger.warning(
        f"Device '{device_name}' not found in enumeration. Using as-is (may be ALSA device name)."
    )
    return device_name
