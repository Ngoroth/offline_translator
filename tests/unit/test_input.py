from unittest.mock import MagicMock, patch
from app.core.input_windows import KeyboardInput


@patch("app.core.input_windows.keyboard")
def test_keyboard_input_press_release(mock_keyboard):
    """Test that KeyboardInput waits for events."""

    # Mock the Listener
    mock_listener_cls = mock_keyboard.Listener
    mock_listener_instance = mock_listener_cls.return_value

    input_handler = KeyboardInput(key_map={"a": "space"})

    # Verify listener was started
    mock_listener_cls.assert_called_once()
    mock_listener_instance.start.assert_called_once()

    # Verify wait_for_press returns the id from queue
    input_handler._press_queue.put("a")
    result = input_handler.wait_for_press()
    assert result == "a"

    # Verify is_pressed
    input_handler._states["a"] = True
    assert input_handler.is_pressed("a") is True
