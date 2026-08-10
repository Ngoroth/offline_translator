import pytest
import asyncio
from unittest.mock import patch
from app.core.input import Role
import sys

# Mock lgpio module before importing app logic if needed,
# or patch it inside the test.
# Since GPIOInput imports lgpio at top level (likely wrapped in try/except),
# we need to be careful.


@pytest.mark.asyncio
async def test_gpio_input_logic():
    """
    Test GPIOInput logic using the MockLGPIO.
    """
    # 1. Setup Mock
    from tests.mocks.mock_gpio import mock_lgpio

    # We need to inject our mock object where GPIOInput expects 'lgpio'
    with patch.dict(sys.modules, {"lgpio": mock_lgpio}):
        # Now we can import/init GPIOInput
        # Note: We need to reload or re-import if it was already imported
        from app.core.input import GPIOInput

        pin_map: dict[Role, int] = {"a": 17, "b": 27}
        gpio_input = GPIOInput(pin_map)

        # Mock loop
        gpio_input._loop = asyncio.get_running_loop()

        # 2. Start (Claims pins)
        gpio_input.start()
        assert len(mock_lgpio.chips) > 0

        # 3. Wait for Press (Role A)
        task = asyncio.create_task(gpio_input.wait_for_press())

        # Simulate Press on Pin 17 (Role A)
        # Assuming we handle logic to detect which handle was opened.
        handle = list(mock_lgpio.chips.keys())[0]
        mock_lgpio.simulate_press(handle, 17)

        role = await asyncio.wait_for(task, timeout=0.1)
        assert role == "a"

        # 4. Wait for Release (Role A)
        task_release = asyncio.create_task(gpio_input.wait_for_release("a"))
        mock_lgpio.simulate_release(handle, 17)
        await asyncio.wait_for(task_release, timeout=0.1)

        # 5. Role B
        task_b = asyncio.create_task(gpio_input.wait_for_press())
        mock_lgpio.simulate_press(handle, 27)
        role = await asyncio.wait_for(task_b, timeout=0.1)
        assert role == "b"

        gpio_input.stop()
