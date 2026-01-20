from typing import Any, Callable, Iterable

class CallbackFlags: ...

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
