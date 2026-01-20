# pyright: reportAny=false
# pyright: reportExplicitAny=false
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field

# We use pydantic directly as BaseSettings might require pydantic-settings package
# which we haven't explicitly checked for, but we added pydantic.
# Let's use standard Pydantic models and a loader.


class HardwareSettings(BaseModel):
    platform: Literal["windows", "rpi", "auto"] = "auto"
    input_mode: Literal["keyboard", "gpio"] = "keyboard"
    audio_input_device_index: int | None = None
    audio_output_device_index: int | None = None


class LLMSettings(BaseModel):
    model_path: str
    n_gpu_layers: int = Field(default=0, description="-1 for all, 0 for CPU")
    n_ctx: int = 4096


class AppSettings(BaseModel):
    hardware: HardwareSettings
    llm: LLMSettings


def load_settings(config_path: Path | None = None) -> AppSettings:
    target_path = config_path or Path("config.yaml")

    if not target_path.exists():
        raise FileNotFoundError(f"Config file not found: {target_path}")

    with open(target_path, "r") as f:
        config_data: dict[str, Any] = yaml.safe_load(f)

    # Handle profile selection
    if "current_profile" in config_data:
        profile = config_data["current_profile"]
        if profile not in config_data.get("profiles", {}):
            raise ValueError(f"Profile '{profile}' not found in config")
        data = config_data["profiles"][profile]
        return AppSettings(**data)

    return AppSettings(**config_data)
