from typing import override
from app.core.input import QueuedInput, Role


class MockInput(QueuedInput):
    """
    Mock input handler for testing.
    Allows manual triggering of press and release events.
    """

    def __init__(self):
        super().__init__()

    def trigger_press(self, role: Role) -> None:
        self.pressed[role] = True
        self._release_events[role].clear()
        self._press_queue.put_nowait(role)

    def trigger_release(self, role: Role) -> None:
        self.pressed[role] = False
        self._release_events[role].set()

    @override
    def start(self) -> None:
        pass

    @override
    def stop(self) -> None:
        pass
