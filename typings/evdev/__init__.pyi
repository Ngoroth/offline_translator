# typings/evdev/__init__.pyi
from typing import AsyncIterator, Any

KEY = {}

class InputEvent:
    type: int
    code: int
    value: int

class InputDevice:
    name: str
    def __init__(self, path: str, *args: Any, **kwargs: Any) -> None: ...
    def async_read_loop(self) -> AsyncIterator[InputEvent]: ...
    def close(self) -> None: ...

class ecodes:
    KEY: dict[int, str | list[str]]
