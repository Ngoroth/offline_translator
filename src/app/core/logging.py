import sys
from pathlib import Path

from loguru import logger


def setup_logging(log_file: str | Path = "logs/app.log") -> None:
    """
    Configure loguru logger.
    - Console: Standard format, stderr.
    - File: JSON format, rotation, retention.
    """
    path = Path(log_file)
    # Ensure directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Remove default handler to avoid duplicate logs if re-configured
    logger.remove()

    # Console sink
    _ = logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )

    # File sink (JSON)
    _ = logger.add(
        str(path),
        rotation="10 MB",
        retention="1 week",
        serialize=True,  # This makes it JSON
        enqueue=True,  # Async safe
        backtrace=True,
        diagnose=True,
    )
