"""System status endpoints."""

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings

router = APIRouter(tags=["system"])


@router.get("/")
async def root(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    """Return basic service identity."""

    return {"status": "running", "project": settings.app_name}


@router.get("/health")
async def health() -> dict[str, str]:
    """Return a liveness response suitable for container orchestration."""

    return {"status": "healthy"}


@router.get("/version")
async def version(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    """Return the deployed application version."""

    return {"version": settings.app_version}
