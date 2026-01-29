from typing import Callable, Any

# Constants for lgpio
RISING_EDGE = 1
FALLING_EDGE = 2
BOTH_EDGES = 3


class MockLGPIO:
    """
    Mock implementation of lgpio library for Windows development and testing.
    """

    RISING_EDGE: int = 1
    FALLING_EDGE: int = 2
    BOTH_EDGES: int = 3

    chips: dict[int, int]
    callbacks: dict[tuple[int, int], Callable[[int, int, int, int], None]]
    pin_states: dict[tuple[int, int], int]
    _handle_counter: int
    _timestamp_counter: int

    def __init__(self):
        self.chips = {}
        self.callbacks = {}  # (handle, pin) -> callback
        self.pin_states = {}  # (handle, pin) -> level
        self._handle_counter = 0
        self._timestamp_counter = 0

    def gpiochip_open(self, chip_id: int) -> int:
        self._handle_counter += 1
        self.chips[self._handle_counter] = chip_id
        return self._handle_counter

    def gpiochip_close(self, handle: int) -> None:
        if handle in self.chips:
            del self.chips[handle]

    def gpio_claim_input(self, handle: int, gpio: int, flags: int = 0) -> None:
        _ = flags
        if handle not in self.chips:
            raise ValueError("Invalid handle")
        self.pin_states[(handle, gpio)] = 0

    def gpio_claim_alert(
        self, handle: int, gpio: int, edge: int, flags: int = 0, infra: int = 0
    ) -> None:
        _ = flags
        _ = infra
        _ = edge
        _ = gpio
        # verifying handle exists
        if handle not in self.chips:
            raise ValueError("Invalid handle")

    def gpio_set_debounce_micros(self, handle: int, gpio: int, debounce_micros: int) -> None:
        _ = handle
        _ = gpio
        _ = debounce_micros
        pass

    def callback(
        self, handle: int, gpio: int, edge: int, func: Callable[[int, int, int, int], None]
    ) -> Any:
        _ = handle
        _ = gpio
        _ = edge
        self.callbacks[(handle, gpio)] = func
        return "callback_obj"

    def callback_cancel(self, cb_obj: Any) -> None:
        _ = cb_obj
        pass

    def _next_timestamp(self) -> int:
        """Generate incrementing timestamps to pass debounce checks (100ms apart)."""
        self._timestamp_counter += 100_000_000  # 100ms in nanoseconds
        return self._timestamp_counter

    # --- Simulation Methods ---
    def simulate_press(self, handle: int, gpio: int):
        """Simulate a button press (Active Low: 1 -> 0) or High if active high."""
        # Assuming Active Low for PTT usually, but let's assume we simulate the *change*
        # lgpio callback signature: (chip, gpio, level, timestamp)

        # Press (Falling Edge for Pull Up)
        if (handle, gpio) in self.callbacks:
            self.callbacks[(handle, gpio)](0, gpio, 0, self._next_timestamp())

    def simulate_release(self, handle: int, gpio: int):
        # Release (Rising Edge for Pull Up)
        if (handle, gpio) in self.callbacks:
            self.callbacks[(handle, gpio)](0, gpio, 1, self._next_timestamp())


# Global instance for patching
mock_lgpio = MockLGPIO()
