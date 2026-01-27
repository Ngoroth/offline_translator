from pathlib import Path

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator
from typing import cast, ClassVar
from pydantic_settings import BaseSettings, SettingsConfigDict


class AudioSettings(BaseModel):
    sample_rate: int = Field(default=16000, gt=0)
    channels: int = Field(default=1, ge=1)
    playback_during_recording: bool = False
    input_device_index: int | None = None
    output_device_index: int | None = None


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

    @field_validator("model_path")
    @classmethod
    def validate_model_path(cls, v: str) -> str:
        if not Path(v).is_file():
            raise ValueError(f"TTS model file not found: {v}")
        return v


class VADSettings(BaseModel):
    threshold_ms: int = Field(default=500, gt=0)
    aggressiveness: int = Field(default=3, ge=0, le=3)


class InputSettings(BaseModel):
    ptt_a: str = "space"
    ptt_b: str = "alt"


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
    speakers: dict[str, SpeakerSettings] = {}


class RootConfig(BaseModel):
    current_profile: str
    profiles: dict[str, dict[str, object]]


def load_settings(config_path: str | Path = "config.yaml") -> AppSettings:
    """
    Load configuration from a YAML file, select the active profile,
    and validate it using AppSettings.
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

    if root.current_profile not in root.profiles:
        raise ValueError(
            f"Active profile '{root.current_profile}' not found in 'profiles'. "
            + f"Available: {list(root.profiles.keys())}"
        )

    profile_data = root.profiles[root.current_profile]

    try:
        # Use model_validate to create AppSettings from the dict
        return AppSettings.model_validate(profile_data)
    except ValidationError as e:
        raise ValueError(f"Invalid configuration for profile '{root.current_profile}': {e}") from e
