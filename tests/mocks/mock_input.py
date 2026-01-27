import asyncio
from typing import override
from app.core.input import BaseInput, Role


class MockInput(BaseInput):
    """
    Mock input handler for testing.
    Allows manual triggering of press and release events.
    """

    # Removed class-level declarations to avoid redeclaration warning.
    # Type hints in __init__ or inferred are sufficient, or use ClassVar if intended.
    # Here they are instance variables.

    def __init__(self):
        self.pressed_state: dict[Role, bool] = {"a": False, "b": False}
        self._press_queue: asyncio.Queue[Role] = asyncio.Queue()
        self._release_events: dict[Role, asyncio.Event] = {
            "a": asyncio.Event(),
            "b": asyncio.Event(),
        }
        self._release_events["a"].set()
        self._release_events["b"].set()

    def trigger_press(self, role: Role):
        self.pressed_state[role] = True
        self._release_events[role].clear()
        self._press_queue.put_nowait(role)

    def trigger_release(self, role: Role):
        self.pressed_state[role] = False
        self._release_events[role].set()

    @override
    async def wait_for_press(self) -> Role:
        return await self._press_queue.get()

    @override
    async def wait_for_release(self, role: Role) -> None:
        await self._release_events[role].wait()

    @override
    def is_pressed(self, role: Role) -> bool:
        return self.pressed_state[role]

    @override
    def start(self) -> None:
        pass

    @override
    def stop(self) -> None:
        pass
