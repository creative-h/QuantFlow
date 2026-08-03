"""Structured application logging."""

import sys
from pathlib import Path

from loguru import logger


def configure_logging(log_level: str, log_directory: Path = Path("logs")) -> None:
    """Configure console, application, and error log sinks."""

    log_directory.mkdir(parents=True, exist_ok=True)
    logger.remove()
    logger.add(sys.stderr, level=log_level, serialize=False, backtrace=False, diagnose=False)
    logger.add(log_directory / "app.log", level=log_level, rotation="00:00", retention="30 days")
    logger.add(log_directory / "errors.log", level="ERROR", rotation="00:00", retention="30 days")
