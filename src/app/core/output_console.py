from typing import override
from app.core.output import OutputProvider
from loguru import logger


class ConsoleOutput(OutputProvider):
    @override
    def status(self, msg: str) -> None:
        print(f"[*] {msg}")
        logger.info(msg)

    @override
    def error(self, msg: str) -> None:
        print(f"[!] ERROR: {msg}")
        logger.error(msg)
