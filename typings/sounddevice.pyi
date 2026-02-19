from typing import Any, Callable, Iterable, TypedDict

class CallbackFlags: ...

class DeviceInfo(TypedDict):
    name: str
    hostapi: int
    max_input_channels: int
    max_output_channels: int
    default_low_input_latency: float
    default_low_output_latency: float
    default_high_input_latency: float
    default_high_output_latency: float
    default_samplerate: float

class Stream:
    def start(self) -> None: ...
    def stop(self) -> None: ...
    def close(self) -> None: ...

class InputStream(Stream):
    def __init__(
        self,
        samplerate: float | None = None,
        device: int | str | None = None,
        channels: int | None = None,
        dtype: Any = None,
        callback: Callable[..., None] | None = None,
        blocksize: int | None = None,
        latency: float | str | None = None,
        extra_settings: Any = None,
    ) -> None: ...

def play(
    data: Any,
    samplerate: float | None = None,
    mapping: Iterable[int] | None = None,
    blocking: bool = False,
    device: int | str | None = None,
    **kwargs: Any,
) -> None: ...
def wait() -> None: ...
def stop() -> None: ...
def query_devices(device: int | str | None = None, kind: str | None = None) -> list[DeviceInfo]: ...

class _DefaultDevice:
    device: tuple[int | None, int | None]

default: _DefaultDevice
