from pathlib import Path
from typing import Literal, cast

import yaml
from pydantic import BaseModel, Field, TypeAdapter

# We use pydantic directly as BaseSettings might require pydantic-settings package
# which we haven't explicitly checked for, but we added pydantic.
# Let's use standard Pydantic models and a loader.


class AudioConfig(BaseModel):
    sample_rate: int = 16000
    channels: int = 1
    input_device_index: int | None = None
    output_device_index: int | None = None
    playback_during_recording: bool = False


class STTConfig(BaseModel):
    model_path: str
    language: str = "en"  # Changed from auto to en for more predictability in simple cases
    beam_size: int = 5


class LLMConfig(BaseModel):
    model_path: str
    n_gpu_layers: int = Field(default=0, description="-1 for all, 0 for CPU")
    n_ctx: int = 4096
    thread_count: int = 4


class TTSConfig(BaseModel):
    model_path: str
    speaker_id: int | None = None


class SpeakerConfig(BaseModel):
    name: str = "Unknown"
    from_lang: str
    to_lang: str
    tts_model: str | None = None


class InputConfig(BaseModel):
    ptt_a: str = "space"
    ptt_b: str = "alt"


class AppSettings(BaseModel):
    audio: AudioConfig = Field(default_factory=AudioConfig)
    stt: STTConfig
    llm: LLMConfig
    tts: TTSConfig
    input: InputConfig = Field(default_factory=InputConfig)
    speakers: dict[str, SpeakerConfig] = Field(default_factory=dict)

    # Legacy/Platform settings (optional, keeping for compatibility if needed)
    platform: Literal["windows", "rpi", "auto"] = "auto"
    input_mode: Literal["keyboard", "gpio"] = "keyboard"


def load_settings(config_path: Path | None = None) -> AppSettings:
    target_path = config_path or Path("config.yaml")

    if not target_path.exists():
        raise FileNotFoundError(f"Config file not found: {target_path}")

    with open(target_path, "r") as f:
        config_data = cast(dict[str, object], yaml.safe_load(f))

    # Handle profile selection
    if "current_profile" in config_data:
        profile = cast(str, config_data["current_profile"])
        profiles = cast(dict[str, dict[str, object]], config_data.get("profiles", {}))
        if profile not in profiles:
            raise ValueError(f"Profile '{profile}' not found in config")
        data = profiles[profile]
        return TypeAdapter(AppSettings).validate_python(data)

    return TypeAdapter(AppSettings).validate_python(config_data)
