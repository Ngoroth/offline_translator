import platform

from app.core.audio.recorder import AudioRecorder
from app.core.audio.recorder_sounddevice import SoundDeviceAudioRecorder

RecorderFactory = type[AudioRecorder] | type[SoundDeviceAudioRecorder]


def _normalize_platform(platform_name: str) -> str:
    normalized = platform_name.strip().lower()
    if normalized in {"windows", "win32"}:
        return "windows"
    if normalized in {"linux", "rpi", "raspberrypi", "raspberry-pi"}:
        return "linux"
    if normalized == "auto":
        host = platform.system().strip().lower()
        if host.startswith("win"):
            return "windows"
        if host == "linux":
            return "linux"
        return "windows"
    return normalized


def select_recorder_factory(platform_name: str) -> RecorderFactory:
    normalized_platform = _normalize_platform(platform_name)
    if normalized_platform == "windows":
        return SoundDeviceAudioRecorder
    return AudioRecorder
