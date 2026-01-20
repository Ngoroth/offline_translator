from typing import Any, Iterable
import numpy as np

class Segment:
    text: str

class TranscriptionInfo:
    language: str
    language_probability: float

class WhisperModel:
    def __init__(
        self,
        model_size_or_path: str,
        device: str = "auto",
        device_index: int | list[int] = 0,
        compute_type: str = "default",
        cpu_threads: int = 0,
        num_workers: int = 1,
        download_root: str | None = None,
        local_files_only: bool = False,
    ) -> None: ...
    def transcribe(
        self,
        audio: str | np.ndarray[Any, Any],
        language: str | None = None,
        task: str = "transcribe",
        beam_size: int = 5,
        **kwargs: Any,
    ) -> tuple[Iterable[Segment], TranscriptionInfo]: ...
