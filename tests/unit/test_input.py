from unittest.mock import MagicMock, patch
import pytest
from app.core.input import KeyboardInput


@pytest.mark.asyncio
async def test_keyboard_input_async_press() -> None:
    """Test that KeyboardInput waits for events asynchronously."""
    with patch("app.core.input.keyboard.Listener") as mock_listener_cls:
        mock_listener_instance = mock_listener_cls.return_value

        # Initialize
        input_handler = KeyboardInput(key_map={"a": "space"})
        input_handler.start()

        # Verify listener started
        mock_listener_cls.assert_called_once()
        mock_listener_instance.start.assert_called_once()

        # Mock loop interaction
        # We need to simulate the callback putting item into queue
        # Since we can't easily trigger the real thread callback into the mock loop
        # without complex setup, we'll manually inject into queue for this test
        # or mock _on_press behavior.

        # Let's test _on_press logic triggering the queue put
        # We need to mock the loop attached to input_handler
        mock_loop = MagicMock()
        setattr(input_handler, "_loop", mock_loop)

        # Simulate Key Press
        mock_key = MagicMock()
        mock_key.name = "space"

        # Trigger internal callback
        # Use getattr to bypass reportPrivateUsage
        on_press = getattr(input_handler, "_on_press")
        on_press(mock_key)

        # Expect call_soon_threadsafe to be called
        assert mock_loop.call_soon_threadsafe.called

        # Now manually put item in queue to test wait_for_press
        # access private _press_queue
        queue = getattr(input_handler, "_press_queue")
        await queue.put("a")

        result = await input_handler.wait_for_press()
        assert result == "a"


def test_keyboard_input_state_tracking() -> None:
    """Test is_pressed state tracking."""
    with patch("app.core.input.keyboard.Listener"):
        input_handler = KeyboardInput(key_map={"a": "space"})

        # Simulate Press
        mock_key = MagicMock()
        mock_key.name = "space"

        on_press = getattr(input_handler, "_on_press")
        on_press(mock_key)
        assert input_handler.is_pressed("a") is True

        # Simulate Release
        on_release = getattr(input_handler, "_on_release")
        on_release(mock_key)
        assert input_handler.is_pressed("a") is False


def test_keyboard_input_key_matching() -> None:
    """Test robust key matching logic."""
    with patch("app.core.input.keyboard.Listener"):
        input_handler = KeyboardInput(key_map={"a": "space", "b": "alt"})

        # Test space (Key.space usually has .name='space')
        mock_space = MagicMock()
        mock_space.name = "space"

        get_role = getattr(input_handler, "_get_role")
        assert get_role(mock_space) == "a"

        # Test alt (could be alt_l)
        mock_alt = MagicMock()
        mock_alt.name = "alt_l"
        assert get_role(mock_alt) == "b"

        # Test unknown
        mock_unknown = MagicMock()
        mock_unknown.name = "f1"
        assert get_role(mock_unknown) is None
