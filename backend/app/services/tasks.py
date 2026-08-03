"""Scheduled task definitions."""

from loguru import logger


async def heartbeat() -> None:
    """Emit a scheduler heartbeat for operations monitoring."""

    logger.info("QuantFlow scheduler heartbeat")
