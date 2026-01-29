import pytest
import asyncio
from app.core.input import KeyboardInput, Role
from pynput import keyboard


@pytest.mark.asyncio
async def test_keyboard_input_mapping_integration():
    """
    Verify that KeyboardInput correctly maps raw pynput keys to Roles
    based on the provided key map configuration.
    """
    # 1. Setup Configuration with specific keys
    key_map: dict[Role, str] = {"a": "space", "b": "alt"}

    input_handler = KeyboardInput(key_map=key_map)
    # Mock the loop to prevent "initialized outside of running loop" warning affecting test logic
    input_handler._loop = asyncio.get_running_loop()

    # 2. Simulate Raw Key Press: SPACE -> Role A
    # Pynput Key.space
    input_handler._on_press(keyboard.Key.space)

    role = await asyncio.wait_for(input_handler.wait_for_press(), timeout=0.1)
    assert role == "a", "Space key should map to Role A"

    # Clear events for next test
    input_handler.pressed["a"] = False

    # 3. Simulate Raw Key Press: LEFT ALT -> Role B
    # Pynput Key.alt_l
    input_handler._on_press(keyboard.Key.alt_l)

    role = await asyncio.wait_for(input_handler.wait_for_press(), timeout=0.1)
    assert role == "b", "Left Alt key should map to Role B"

    # Clear events
    input_handler.pressed["b"] = False

    # 4. Simulate Raw Key Press: RIGHT ALT -> Role B
    # Pynput Key.alt_r
    input_handler._on_press(keyboard.Key.alt_r)

    role = await asyncio.wait_for(input_handler.wait_for_press(), timeout=0.1)
    assert role == "b", "Right Alt key should map to Role B"

    # 5. Simulate Unmapped Key -> Ignored
    input_handler._on_press(keyboard.Key.shift)

    try:
        await asyncio.wait_for(input_handler.wait_for_press(), timeout=0.1)
        pytest.fail("Unmapped key should not trigger wait_for_press")
    except asyncio.TimeoutError:
        pass  # Expected behavior
