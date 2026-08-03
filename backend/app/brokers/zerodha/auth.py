"""Kite authentication service wrapper for backward compatibility."""

from app.core.config import Settings
from app.services.zerodha_auth import ZerodhaAuthService


class KiteAuthService:
    """Exchanges a short-lived Kite request token for a session token."""

    def __init__(self, settings: Settings) -> None:
        self._service = ZerodhaAuthService(settings)

    async def exchange_request_token(self, request_token: str) -> str:
        """Return the Kite access token for a successful login callback."""
        session_data = await self._service.exchange_token(request_token)
        return str(session_data["access_token"])
