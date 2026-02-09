import asyncio
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Literal, override

from loguru import logger

if TYPE_CHECKING:
    from pynput import keyboard as pynput_keyboard

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
    """Windows/Linux keyboard input using pynput (requires X server on Linux)."""

    key_map: dict[Role, str]
    pressed: dict[Role, bool]
    _press_queue: asyncio.Queue[Role]
    _release_events: dict[Role, asyncio.Event]
    _loop: asyncio.AbstractEventLoop
    _listener: "pynput_keyboard.Listener | None"

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
        from pynput import keyboard

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

    def _on_press(self, key: "pynput_keyboard.Key | pynput_keyboard.KeyCode | None") -> None:
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

    def _on_release(self, key: "pynput_keyboard.Key | pynput_keyboard.KeyCode | None") -> None:
        try:
            role = self._get_role(key)
            if role:
                if self.pressed[role]:
                    self.pressed[role] = False
                    _ = self._loop.call_soon_threadsafe(self._release_events[role].set)
        except Exception as e:
            logger.error(f"Input release error: {e}")

    def _get_role(self, key: "pynput_keyboard.Key | pynput_keyboard.KeyCode | None") -> Role | None:
        from pynput import keyboard

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


class EvdevInput(BaseInput):
    """
    Linux evdev input for USB keyboards/numpads (headless, no X required).
    Uses the `evdev` library to read input events directly from /dev/input/eventX.
    """

    device_path: str
    key_map: dict[Role, str]
    pressed: dict[Role, bool]
    _press_queue: asyncio.Queue[Role]
    _release_events: dict[Role, asyncio.Event]
    _loop: asyncio.AbstractEventLoop
    _reader_task: asyncio.Task[None] | None
    _stop_event: asyncio.Event

    def __init__(self, device_path: str, key_map: dict[Role, str]):
        self.device_path = device_path
        self.key_map = key_map
        self.pressed = {"a": False, "b": False}
        self._press_queue = asyncio.Queue()
        self._release_events = {"a": asyncio.Event(), "b": asyncio.Event()}
        self._release_events["a"].set()
        self._release_events["b"].set()
        self._reader_task = None
        self._stop_event = asyncio.Event()

        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            logger.warning("EvdevInput initialized outside of running loop.")

    @override
    def start(self) -> None:
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            logger.error("EvdevInput.start() must be called from within an async context.")
            return

        self._stop_event.clear()
        self._reader_task = self._loop.create_task(self._read_events())
        logger.info(f"Evdev input listener started on {self.device_path}")

    @override
    def stop(self) -> None:
        self._stop_event.set()
        if self._reader_task:
            _ = self._reader_task.cancel()
            self._reader_task = None
        logger.info("Evdev input listener stopped")

    async def _read_events(self) -> None:
        try:
            import evdev  # pyright: ignore[reportMissingImports]
        except ImportError:
            logger.error("evdev library not found. Install with: pip install evdev")
            return

        try:
            device = evdev.InputDevice(self.device_path)
            logger.info(f"Opened evdev device: {device.name}")
        except Exception as e:
            logger.error(f"Failed to open evdev device {self.device_path}: {e}")
            return

        try:
            async for event in device.async_read_loop():
                if self._stop_event.is_set():
                    break

                # EV_KEY = 1
                if event.type != 1:
                    continue

                key_name_raw = evdev.ecodes.KEY.get(event.code, f"KEY_{event.code}")
                if isinstance(key_name_raw, list):
                    key_name = str(key_name_raw[0])
                else:
                    key_name = str(key_name_raw)

                # DEBUG LOG
                if event.value == 1:
                    logger.debug(f"Evdev key detected: {key_name} (code: {event.code})")

                role = self._get_role(key_name)
                if not role:
                    continue

                # value: 1 = press, 0 = release, 2 = hold/repeat
                if event.value == 1:  # Press
                    if not self.pressed[role]:
                        self.pressed[role] = True
                        self._release_events[role].clear()
                        await self._press_queue.put(role)
                elif event.value == 0:  # Release
                    if self.pressed[role]:
                        self.pressed[role] = False
                        self._release_events[role].set()

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Evdev read error: {e}")
        finally:
            device.close()

    def _get_role(self, key_name: str) -> Role | None:
        for role, configured_key in self.key_map.items():
            if key_name.upper() == configured_key.upper():
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
    Raspberry Pi GPIO implementation using `lgpio`.
    Supports active low configuration (default for PTT).
    """

    pin_map: dict[Role, int]
    pressed: dict[Role, bool]
    chip_id: int
    handle: int | None
    _press_queue: asyncio.Queue[Role]
    _release_events: dict[Role, asyncio.Event]
    _loop: asyncio.AbstractEventLoop
    _last_event_time: dict[Role, float]
    debounce_ns: int

    def __init__(self, pin_map: dict[Role, int], chip_id: int = 0, debounce_ms: int = 50):
        self.pin_map = pin_map
        self.pressed = {"a": False, "b": False}
        self.chip_id = chip_id
        self.handle = None
        self._press_queue = asyncio.Queue()
        self._release_events = {"a": asyncio.Event(), "b": asyncio.Event()}
        self._release_events["a"].set()
        self._release_events["b"].set()
        self._last_event_time = {"a": 0.0, "b": 0.0}
        self.debounce_ns = debounce_ms * 1_000_000  # ms to ns

        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            logger.warning("GPIOInput initialized outside of running loop.")

    @override
    def start(self) -> None:
        try:
            import lgpio
        except ImportError:
            logger.error("lgpio library not found. GPIO input will not function.")
            return

        try:
            self.handle = lgpio.gpiochip_open(self.chip_id)
            logger.info(f"Opened GPIO chip {self.chip_id} (Handle: {self.handle})")

            for role, pin in self.pin_map.items():
                # Claim input
                lgpio.gpio_claim_input(self.handle, pin)
                # Set alert for both edges (Press & Release)
                lgpio.gpio_claim_alert(self.handle, pin, lgpio.BOTH_EDGES, flags=0, infra=0)
                # Register callback for this pin
                _ = lgpio.callback(self.handle, pin, lgpio.BOTH_EDGES, self._gpio_callback)
                logger.info(f"GPIO Pin {pin} claimed for Role {role}")

        except Exception as e:
            logger.error(f"Failed to initialize GPIO: {e}")
            if self.handle is not None:
                lgpio.gpiochip_close(self.handle)
                self.handle = None

    @override
    def stop(self) -> None:
        if self.handle is not None:
            try:
                import lgpio

                lgpio.gpiochip_close(self.handle)
                logger.info("GPIO chip closed")
            except Exception as e:
                logger.error(f"Error closing GPIO: {e}")
            finally:
                self.handle = None

    def _gpio_callback(self, chip: int, gpio: int, level: int, timestamp: int) -> None:
        """
        Callback from lgpio (runs in a separate thread).
        level: 0 (Low), 1 (High), 2 (Watchdog)
        """
        # Suppress unused variable warnings
        _ = chip
        _ = timestamp

        role: Role | None = None
        for r, pin in self.pin_map.items():
            if pin == gpio:
                role = r
                break

        if not role:
            return

        # Software Debounce
        # timestamp is in nanoseconds (from lgpio)
        last_time = self._last_event_time[role]
        if timestamp - last_time < self.debounce_ns:
            return  # Ignore noise

        self._last_event_time[role] = float(timestamp)

        # Assuming Active Low (0 = Pressed, 1 = Released)
        # TODO: Make this configurable via GPIOSettings
        is_pressed_now = level == 0

        if is_pressed_now:
            if not self.pressed[role]:
                self.pressed[role] = True
                self._release_events[role].clear()
                # Notify main loop
                _ = self._loop.call_soon_threadsafe(self._press_queue.put_nowait, role)
        else:
            if self.pressed[role]:
                self.pressed[role] = False
                _ = self._loop.call_soon_threadsafe(self._release_events[role].set)

    @override
    async def wait_for_press(self) -> Role:
        return await self._press_queue.get()

    @override
    async def wait_for_release(self, role: Role) -> None:
        _ = await self._release_events[role].wait()

    @override
    def is_pressed(self, role: Role) -> bool:
        return self.pressed.get(role, False)
