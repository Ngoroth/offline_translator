import asyncio
from abc import ABC, abstractmethod
from typing import Literal, override

from loguru import logger
from pynput import keyboard

Role = Literal["a", "b"]
EventType = Literal["press", "release"]


class BaseInput(ABC):
    @abstractmethod
    async def wait_for_press(self) -> Role:
        """
        Wait asynchronously until a PTT button is pressed.
        Returns 'a' or 'b' indicating which button was pressed.
        """
        pass

    @abstractmethod
    async def wait_for_release(self, role: Role) -> None:
        """
        Wait asynchronously until the PTT button for the given role is released.
        """
        pass

    @abstractmethod
    def is_pressed(self, role: Role) -> bool:
        """
        Check if the button for the given role is currently held down.
        """
        pass

    @abstractmethod
    def start(self) -> None:
        """Start the input listener."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop the input listener."""
        pass


class KeyboardInput(BaseInput):
    key_map: dict[Role, str]
    pressed: dict[Role, bool]
    _press_queue: asyncio.Queue[Role]
    _release_events: dict[Role, asyncio.Event]
    _loop: asyncio.AbstractEventLoop
    _listener: keyboard.Listener | None

    def __init__(self, key_map: dict[Role, str]):
        self.key_map = key_map
        self.pressed = {"a": False, "b": False}
        self._press_queue = asyncio.Queue()
        self._release_events = {"a": asyncio.Event(), "b": asyncio.Event()}
        # Ensure events are set initially (since not pressed)
        self._release_events["a"].set()
        self._release_events["b"].set()
        self._listener = None

        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            logger.warning("KeyboardInput initialized outside of running loop.")

    @override
    def start(self) -> None:
        if self._listener:
            return
        # Start the listener in a non-blocking way
        self._listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
        self._listener.start()
        logger.info("Keyboard input listener started")

    @override
    def stop(self) -> None:
        if self._listener:
            self._listener.stop()
            self._listener = None
        logger.info("Keyboard input listener stopped")

    def _on_press(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        try:
            role = self._get_role(key)
            if role:
                if not self.pressed[role]:
                    self.pressed[role] = True
                    self._release_events[role].clear()
                    # Notify async loop
                    _ = self._loop.call_soon_threadsafe(self._press_queue.put_nowait, role)
        except Exception as e:
            logger.error(f"Input press error: {e}")

    def _on_release(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        try:
            role = self._get_role(key)
            if role:
                if self.pressed[role]:
                    self.pressed[role] = False
                    _ = self._loop.call_soon_threadsafe(self._release_events[role].set)
        except Exception as e:
            logger.error(f"Input release error: {e}")

    def _get_role(self, key: keyboard.Key | keyboard.KeyCode | None) -> Role | None:
        if key is None:
            return None

        k_str = ""
        if isinstance(key, keyboard.KeyCode):
            if key.char:
                k_str = key.char.lower()
            else:
                k_str = str(key)
        else:
            k_str = key.name

        for role, configured_key in self.key_map.items():
            conf = configured_key.lower()
            if k_str == conf:
                return role
            if conf == "alt" and k_str in ("alt_l", "alt_r"):
                return role
            if conf == "ctrl" and k_str in ("ctrl_l", "ctrl_r"):
                return role

        return None

    @override
    async def wait_for_press(self) -> Role:
        return await self._press_queue.get()

    @override
    async def wait_for_release(self, role: Role) -> None:
        _ = await self._release_events[role].wait()

    @override
    def is_pressed(self, role: Role) -> bool:
        return self.pressed.get(role, False)


class GPIOInput(BaseInput):
    """
    Placeholder for Raspberry Pi GPIO implementation (Story 3.1).
    """

    def __init__(self, _pin_map: dict[Role, int]):
        logger.warning("GPIOInput is not fully implemented yet.")

    @override
    def start(self) -> None:
        pass

    @override
    def stop(self) -> None:
        pass

    @override
    async def wait_for_press(self) -> Role:
        # Placeholder that never returns to prevent crashes but signal lack of implementation
        _ = await asyncio.Event().wait()
        return "a"

    @override
    async def wait_for_release(self, role: Role) -> None:
        _ = await asyncio.Event().wait()

    @override
    def is_pressed(self, role: Role) -> bool:
        return False
