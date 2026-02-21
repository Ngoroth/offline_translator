from pathlib import Path

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator
from typing import cast, ClassVar
from pydantic_settings import BaseSettings, SettingsConfigDict


class AudioSettings(BaseModel):
    sample_rate: int = Field(default=16000, gt=0)
    channels: int = Field(default=1, ge=1)
    playback_during_recording: bool = False
    input_device_index: int | None = None
    output_device_index: int | None = None
    # String device names for ALSA (e.g., "plughw:1,0", "default:CARD=Device")
    input_device: str | None = None
    output_device: str | None = None


class STTSettings(BaseModel):
    model_path: str = Field(..., min_length=1)
    language: str = "en"
    beam_size: int = Field(default=5, ge=1)
    device: str = Field(default="cpu", pattern=r"^(cpu|cuda)$")
    compute_type: str = Field(default="int8", pattern=r"^(int8|float16|float32|int16)$")


class LLMSettings(BaseModel):
    model_path: str = Field(..., min_length=1)
    n_gpu_layers: int = -1
    context_window: int = Field(default=2048, ge=512)
    n_threads: int = Field(default=4, ge=1)

    @field_validator("model_path")
    @classmethod
    def validate_model_path(cls, v: str) -> str:
        if not v.endswith(".gguf"):
            raise ValueError("Model path must end with .gguf")
        return v


class TTSSettings(BaseModel):
    model_path: str = Field(..., min_length=1)
    speaker_id: int | None = None
    sample_rate: int | None = Field(default=None, gt=0)


class VADSettings(BaseModel):
    threshold_ms: int = Field(default=500, gt=0)
    aggressiveness: int = Field(default=3, ge=0, le=3)
    auto_harvest: bool = Field(
        default=True,
        description="Automatically harvest segments on silence. Set to False for PTT-only mode.",
    )


class GPIOSettings(BaseModel):
    chip_id: int = 0
    pin_a: int = 17
    pin_b: int = 27
    debounce_ms: int = 50
    active_low: bool = True  # True = Press is 0 (Ground), Release is 1 (3.3V)


class EvdevSettings(BaseModel):
    """Settings for evdev input (Linux USB keyboards/numpads without X server)."""

    device_path: str | None = None
    device_name: str | None = None  # e.g. "SIGMACHIP USB Keyboard"


class InputSettings(BaseModel):
    # Legacy PTT settings - use speaker_a_key/speaker_b_key in AppSettings instead
    # TODO: Remove in future version when all configs migrated to new format
    ptt_a: str | int = "space"
    ptt_b: str | int = "alt"


class SpeakerSettings(BaseModel):
    from_lang: str = Field(..., min_length=1)
    to_lang: str = Field(..., min_length=1)
    name: str | None = None
    tts_model: str | None = None


class AppSettings(BaseSettings):
    """
    Main application settings representing a single profile.
    Inherits from BaseSettings to satisfy pydantic-settings requirement.
    """

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_prefix="APP_", case_sensitive=False
    )

    platform: str = "auto"
    input_mode: str = "keyboard"
    audio: AudioSettings = AudioSettings()
    stt: STTSettings
    llm: LLMSettings
    tts: TTSSettings
    vad: VADSettings = VADSettings()
    input: InputSettings = InputSettings()
    gpio: GPIOSettings = GPIOSettings()
    evdev: EvdevSettings = EvdevSettings()
    speakers: dict[str, SpeakerSettings] = {}

    # Dual Speaker Role Settings
    speaker_a_key: str | int = "space"
    speaker_b_key: str | int = "alt_r"
    speaker_a_lang: str = "en"
    speaker_b_lang: str = "ru"

    # Voice paths should be set to actual .onnx file paths in config.yaml
    # Empty string means use the default TTS model from tts.model_path
    speaker_a_voice: str = ""
    speaker_b_voice: str = ""

    @model_validator(mode="after")
    def validate_speaker_keys(self) -> "AppSettings":
        """Ensure speaker keys are distinct."""
        if str(self.speaker_a_key).lower() == str(self.speaker_b_key).lower():
            raise ValueError(
                f"Speaker keys must be distinct. Both are set to '{self.speaker_a_key}'"
            )
        return self


class RootConfig(BaseModel):
    current_profile: str
    profiles: dict[str, dict[str, object]]


def load_settings(
    config_path: str | Path = "config.yaml", profile_override: str | None = None
) -> AppSettings:
    """
    Load configuration from a YAML file, select the active profile,
    and validate it using AppSettings.

    When provided, profile_override takes precedence over current_profile
    for this load call only.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        try:
            data = cast(object, yaml.safe_load(f))
        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse config YAML: {e}") from e

    if not isinstance(data, dict):
        raise ValueError("Config file must be a YAML dictionary")

    # Validate root structure
    try:
        root = RootConfig.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"Invalid root configuration structure: {e}") from e

    active_profile = profile_override if profile_override is not None else root.current_profile

    if active_profile not in root.profiles:
        available_profiles = sorted(root.profiles.keys())
        raise ValueError(
            f"Profile '{active_profile}' not found in 'profiles'. "
            + f"Available: {available_profiles}"
        )

    profile_data = root.profiles[active_profile]

    try:
        # Use model_validate to create AppSettings from the dict
        return AppSettings.model_validate(profile_data)
    except ValidationError as e:
        raise ValueError(f"Invalid configuration for profile '{active_profile}': {e}") from e
