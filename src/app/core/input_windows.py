from threading import Event
from queue import Queue
from pynput import keyboard
from typing import override
from app.core.input import InputProvider


class KeyboardInput(InputProvider):
    _press_queue: Queue[str]
    _states: dict[str, bool]
    _key_map: dict[str, str]
    _listener: keyboard.Listener
    _release_events: dict[str, Event]

    def __init__(self, key_map: dict[str, str]):
        """
        Initialize with a mapping of ID to key name.
        Example: {'a': 'space', 'b': 'alt'}
        """
        self._key_map = key_map
        self._press_queue = Queue()
        self._states = {k: False for k in key_map}
        self._release_events = {k: Event() for k in key_map}

        self._listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
        _ = self._listener.start()

    def _on_press(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        if key is None:
            return
        for input_id, target in self._key_map.items():
            if self._is_key_match(key, target):
                if not self._states[input_id]:
                    self._states[input_id] = True
                    self._release_events[input_id].clear()
                    self._press_queue.put(input_id)

    def _on_release(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        if key is None:
            return
        for input_id, target in self._key_map.items():
            if self._is_key_match(key, target):
                self._states[input_id] = False
                self._release_events[input_id].set()

    def _is_key_match(self, key: keyboard.Key | keyboard.KeyCode, target_name: str) -> bool:
        if target_name == "space" and key == keyboard.Key.space:
            return True
        if target_name == "alt" and (
            key == keyboard.Key.alt or key == keyboard.Key.alt_l or key == keyboard.Key.alt_r
        ):
            return True
        if hasattr(key, "char") and getattr(key, "char") == target_name:
            return True
        return False

    @override
    def wait_for_press(self) -> str:
        return self._press_queue.get()

    @override
    def wait_for_release(self, input_id: str) -> None:
        if input_id in self._release_events:
            _ = self._release_events[input_id].wait()

    @override
    def is_pressed(self, input_id: str) -> bool:
        return self._states.get(input_id, False)
