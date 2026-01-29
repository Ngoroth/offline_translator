import pytest
import asyncio
from app.core.input import KeyboardInput, Role
from pynput import keyboard


@pytest.mark.asyncio
async def test_keyboard_input_mapping():
    """
    Verify that KeyboardInput correctly maps physical keys to roles 'a' and 'b'
    based on the provided key_map, including special keys like 'alt_r'.
    """
    key_map: dict[Role, str] = {"a": "space", "b": "alt_r"}
    inp = KeyboardInput(key_map)
    # We need to ensure the loop is set because __init__ might not catch it if not running?
    # Actually __init__ does: self._loop = asyncio.get_running_loop()
    # In pytest-asyncio, the loop is running.

    # Simulate Space press (Role A)
    # pynput Key.space
    inp._on_press(keyboard.Key.space)

    # wait_for_press should return 'a'
    role = await asyncio.wait_for(inp.wait_for_press(), timeout=1.0)
    assert role == "a"

    # Simulate Alt_R press (Role B)
    # pynput Key.alt_r
    inp._on_press(keyboard.Key.alt_r)

    role = await asyncio.wait_for(inp.wait_for_press(), timeout=1.0)
    assert role == "b"


@pytest.mark.asyncio
async def test_keyboard_input_mapping_generic_alt():
    """
    Verify that 'alt' in config maps to both alt_l and alt_r.
    """
    key_map: dict[Role, str] = {"a": "space", "b": "alt"}
    inp = KeyboardInput(key_map)

    # Alt_L -> b
    inp._on_press(keyboard.Key.alt_l)
    role = await asyncio.wait_for(inp.wait_for_press(), timeout=1.0)
    assert role == "b"

    # Release Alt_L so 'b' is no longer pressed
    inp._on_release(keyboard.Key.alt_l)

    # Alt_R -> b
    inp._on_press(keyboard.Key.alt_r)
    role = await asyncio.wait_for(inp.wait_for_press(), timeout=1.0)
    assert role == "b"
