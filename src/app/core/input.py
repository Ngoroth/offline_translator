from abc import ABC, abstractmethod


class InputProvider(ABC):
    @abstractmethod
    def wait_for_press(self) -> str:
        """
        Block until one of the configured inputs is activated.
        Returns the ID of the activated input (e.g., 'a' or 'b').
        """
        pass

    @abstractmethod
    def wait_for_release(self, input_id: str) -> None:
        """Block until the specified input is deactivated."""
        pass

    @abstractmethod
    def is_pressed(self, input_id: str) -> bool:
        """Check if the specified input is currently active."""
        pass
