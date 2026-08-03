"""Async scheduler lifecycle."""

from apscheduler.schedulers.asyncio import AsyncIOScheduler


def build_scheduler() -> AsyncIOScheduler:
    """Create, but do not yet start, the application scheduler."""

    return AsyncIOScheduler(timezone="Asia/Kolkata")
