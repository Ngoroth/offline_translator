from abc import ABC, abstractmethod


class OutputProvider(ABC):
    @abstractmethod
    def status(self, msg: str) -> None:
        """Display a status message to the user."""
        pass

    @abstractmethod
    def error(self, msg: str) -> None:
        """Display an error message to the user."""
        pass
