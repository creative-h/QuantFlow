"""Broker authentication routers and callbacks."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger

from app.api.dependencies import get_zerodha_auth_service
from app.services.zerodha_auth import ZerodhaAuthService

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/login")
async def login(
    auth_service: ZerodhaAuthService = Depends(get_zerodha_auth_service),
) -> dict[str, Any]:
    """Generate and return the Zerodha Kite login URL."""
    logger.info("Handling GET /auth/login request")
    login_url = auth_service.get_login_url()
    return {"status": "success", "login_url": login_url}


@router.get("/callback")
async def callback(
    request_token: str | None = Query(default=None),
    status: str | None = Query(default=None),
    auth_service: ZerodhaAuthService = Depends(get_zerodha_auth_service),
) -> dict[str, Any]:
    """Handle Zerodha OAuth callback, exchange request_token, and save session."""
    logger.info("Handling GET /auth/callback request")

    if status and status.lower() != "success":
        logger.warning("Callback received non-success status: {}", status)
        raise HTTPException(status_code=401, detail=f"Kite authentication was not successful: {status}")

    if not request_token:
        logger.warning("Callback missing request_token parameter")
        raise HTTPException(status_code=400, detail="Missing request_token parameter")

    try:
        session_data = await auth_service.exchange_token(request_token)
        return {
            "status": "success",
            "message": "Kite session established",
            "user_id": session_data.get("user_id"),
            "user_name": session_data.get("user_name"),
        }
    except Exception as error:
        logger.exception("Kite login callback failed during token exchange")
        raise HTTPException(
            status_code=502, detail=f"Unable to establish Kite session: {error}"
        ) from error


@router.get("/profile")
async def profile(
    auth_service: ZerodhaAuthService = Depends(get_zerodha_auth_service),
) -> dict[str, Any]:
    """Fetch user profile for the current Zerodha session."""
    logger.info("Handling GET /auth/profile request")
    try:
        user_profile = await auth_service.get_profile()
        return {"status": "success", "data": user_profile}
    except ValueError as error:
        logger.warning("Profile request unauthenticated: {}", str(error))
        raise HTTPException(status_code=401, detail=str(error)) from error
    except Exception as error:
        logger.exception("Failed to fetch Zerodha profile")
        raise HTTPException(
            status_code=502, detail=f"Failed to fetch profile: {error}"
        ) from error


@router.post("/logout")
async def logout(
    auth_service: ZerodhaAuthService = Depends(get_zerodha_auth_service),
) -> dict[str, Any]:
    """Terminate the Zerodha session and remove saved session data."""
    logger.info("Handling POST /auth/logout request")
    success = auth_service.clear_session()
    if not success:
        logger.error("Failed to clear session file during logout")
        raise HTTPException(status_code=500, detail="Failed to clear session file")
    return {"status": "success", "message": "Logged out successfully"}


@router.post("/postback")
async def postback() -> dict[str, str]:
    """Acknowledge Kite order-update postbacks."""
    logger.info("Handling POST /auth/postback request")
    return {"message": "postback received"}
