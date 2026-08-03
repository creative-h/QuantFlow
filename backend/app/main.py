"""QuantFlow FastAPI application factory."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from app.api.dependencies import get_live_paper_engine
from app.api.routers import auth, market, paper, system
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.services.scheduler import build_scheduler
from app.services.tasks import heartbeat


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Configure logging, live paper session recovery, and background services."""

    settings = get_settings()
    configure_logging(settings.log_level)
    scheduler = build_scheduler()
    scheduler.add_job(heartbeat, "interval", minutes=5, id="heartbeat")
    scheduler.start()
    application.state.scheduler = scheduler

    # Recover live paper session if session file exists
    live_engine = get_live_paper_engine()
    if live_engine.recover_session():
        logger.info("Live paper session recovered successfully")

    logger.info("{} {} started", settings.app_name, settings.app_version)
    yield

    scheduler.shutdown(wait=False)
    await live_engine.stop()
    logger.info("QuantFlow stopped")


def create_app() -> FastAPI:
    """Build the configured ASGI application."""

    settings = get_settings()
    application = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
    application.include_router(system.router)
    application.include_router(auth.router)
    application.include_router(market.router)
    application.include_router(paper.router)
    return application


app = create_app()
