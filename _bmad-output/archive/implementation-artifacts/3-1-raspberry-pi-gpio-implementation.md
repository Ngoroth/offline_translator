# Story 3.1: Raspberry Pi GPIO Implementation

Status: ready-for-dev

## Story

As a Maker,
I want to use physical buttons connected to the Raspberry Pi GPIO pins,
So that I can build a dedicated hardware device without a keyboard.

## Acceptance Criteria

1.  **Given** The application is running on a Raspberry Pi (detected via config or OS check)
2.  **When** I configure `input_mode: gpio` in `config.yaml`
3.  **Then** The system should load the `GPIOInput` class instead of `KeyboardInput`
4.  **And** Pressing the physical button connected to the defined PIN should trigger PTT actions
5.  **And** It should handle switch debounce logic to prevent phantom presses
6.  **And** It should support "Pull-Up" or "Pull-Down" resistor configuration via software

## Tasks / Subtasks

- [ ] **Technical Preparation: GPIO Mock**
    - [ ] Create `tests/mocks/mock_gpio.py` to simulate `lgpio` or `RPi.GPIO` library.
    - [ ] Ensure mock supports interrupt callbacks (falling/rising edge).
    - [ ] Create `tests/unit/test_gpio_input.py` to verify logic against the mock.

- [ ] **Implement GPIOInput Class**
    - [ ] Update `src/app/core/input.py`: Implement `GPIOInput` class inheriting `BaseInput`.
    - [ ] Use `lgpio` (preferred for modern RPi 5) or `RPi.GPIO` (legacy) - decided: `lgpio` for RPi 5 support.
    - [ ] Implement `wait_for_press` and `wait_for_release` using async compatible event loop integration (e.g., `add_event_detect` with callback that sets an `asyncio.Event`).
    - [ ] Implement software debounce (e.g., ignore events within X ms of previous).

- [ ] **Configuration Updates**
    - [ ] Update `src/app/core/config.py` (`InputSettings`) to include:
        - `gpio_pin_a`: int (default 17)
        - `gpio_pin_b`: int (default 27)
        - `debounce_time_ms`: int (default 50)
    - [ ] Update `config.yaml` with GPIO section.

- [ ] **Integration**
    - [ ] Update `get_input_handler` in `src/app/main.py` to initialize `GPIOInput` when `input_mode="gpio"`.
    - [ ] Ensure graceful failure if GPIO library is missing (e.g., running on Windows with gpio config).

## Dev Notes

### Architecture & Tech Stack

-   **Library**: `lgpio` is standard for RPi 5. `RPi.GPIO` is deprecated for 5.
-   **Dependency**: Add `lgpio` to `pyproject.toml` as optional or handle `ImportError`. Since we develop on Windows, we cannot install `lgpio` easily. **Strategy**: Wrap import in try/except and use Mock if failed, but log warning.
-   **Async Integration**: GPIO callbacks run in a separate thread. Use `loop.call_soon_threadsafe` to set the `asyncio.Event`.

### References

-   `src/app/core/input.py` (Base Class)
-   `config.yaml` (Input Config)
