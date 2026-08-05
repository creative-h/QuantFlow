"""Zerodha Kite Connect Authentication Service."""

import json
from pathlib import Path
from typing import Any, Optional

import httpx
from loguru import logger

from app.core.config import Settings
from app.core.security import kite_checksum


class ZerodhaAuthService:
    """Service handling Zerodha OAuth flow, token exchange, profile retrieval, and session storage."""

    def __init__(
        self,
        settings: Optional[Settings] = None,
        session_file: Path | str | None = None,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self.settings = settings or Settings()
        if session_file is None:
            # Save session in backend/data/session.json
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.session_file = base_dir / "data" / "session.json"
        else:
            self.session_file = Path(session_file)
        self.client = client

    def get_login_url(self) -> str:
        """Generate Zerodha OAuth login URL."""
        api_key = self.settings.zerodha_api_key
        redirect_url = self.settings.zerodha_redirect_url
        logger.info("Generating Zerodha login URL")
        url = f"https://kite.zerodha.com/connect/login?v=3&api_key={api_key}"
        if redirect_url:
            url += f"&redirect_url={redirect_url}"
        return url

    async def exchange_token(self, request_token: str) -> dict[str, Any]:
        """Exchange short-lived request_token for access_token and session data."""
        logger.info("Exchanging request_token for Zerodha access_token")

        # Calculate checksum using API key, request_token, and API secret
        checksum = kite_checksum(
            self.settings.zerodha_api_key,
            request_token,
            self.settings.zerodha_api_secret,
        )
        payload = {
            "api_key": self.settings.zerodha_api_key,
            "request_token": request_token,
            "checksum": checksum,
        }
        headers = {"X-Kite-Version": "3"}
        url = "https://api.kite.trade/session/token"

        try:
            if self.client:
                response = await self.client.post(url, data=payload, headers=headers)
            else:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    response = await client.post(url, data=payload, headers=headers)

            response.raise_for_status()
            res_json = response.json()
        except httpx.HTTPStatusError as err:
            logger.error("Token exchange failed with HTTP status {}", err.response.status_code)
            detail = "Token exchange failed"
            try:
                err_data = err.response.json()
                detail = err_data.get("message", detail)
            except Exception:
                pass
            raise RuntimeError(detail) from err
        except Exception as err:
            logger.error("Token exchange failed with error: {}", str(err))
            raise RuntimeError(f"Token exchange failed: {err}") from err

        if res_json.get("status") != "success" or "data" not in res_json:
            logger.error("Token exchange returned non-success status in body")
            raise RuntimeError(res_json.get("message", "Token exchange failed"))

        session_data = res_json["data"]
        logger.info("Successfully authenticated user_id: {}", session_data.get("user_id", "unknown"))

        # Save session to backend/data/session.json
        self.save_session(session_data)
        return session_data

    def save_session(self, session_data: dict[str, Any]) -> None:
        """Save session data securely to session file."""
        self.session_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.session_file, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2)
        logger.info("Saved Zerodha session securely to {}", self.session_file)

    def load_session(self) -> Optional[dict[str, Any]]:
        """Load session data from session file."""
        if not self.session_file.exists():
            logger.warning("Session file does not exist at {}", self.session_file)
            return None
        try:
            with open(self.session_file, "r", encoding="utf-8") as f:
                session_data = json.load(f)
            logger.info("Loaded active Zerodha session for user_id: {}", session_data.get("user_id", "unknown"))
            return session_data
        except Exception as err:
            logger.error("Error loading session file {}: {}", self.session_file, str(err))
            return None

    def is_authenticated(self) -> bool:
        """Return True if session exists with valid access token."""
        session = self.load_session()
        return session is not None and "access_token" in session

    def clear_session(self) -> bool:
        """Remove the session file on logout."""
        if self.session_file.exists():
            try:
                self.session_file.unlink()
                logger.info("Cleared Zerodha session file {}", self.session_file)
                return True
            except Exception as err:
                logger.error("Error clearing session file {}: {}", self.session_file, str(err))
                return False
        logger.info("Session file {} already clear", self.session_file)
        return True

    async def get_profile(self) -> dict[str, Any]:
        """Fetch user profile from Zerodha API using stored session access_token."""
        session = self.load_session()
        if not session or "access_token" not in session:
            logger.warning("Attempted to fetch profile without active session")
            raise ValueError("No active Zerodha session found. Please log in.")

        access_token = session["access_token"]
        api_key = self.settings.zerodha_api_key
        headers = {
            "X-Kite-Version": "3",
            "Authorization": f"token {api_key}:{access_token}",
        }
        url = "https://api.kite.trade/user/profile"

        try:
            if self.client:
                response = await self.client.get(url, headers=headers)
            else:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    response = await client.get(url, headers=headers)

            response.raise_for_status()
            res_json = response.json()
        except httpx.HTTPStatusError as err:
            logger.error("Profile request failed with HTTP status {}", err.response.status_code)
            detail = "Failed to fetch profile"
            try:
                err_data = err.response.json()
                detail = err_data.get("message", detail)
            except Exception:
                pass
            raise RuntimeError(detail) from err
        except Exception as err:
            logger.error("Profile request failed with error: {}", str(err))
            raise RuntimeError(f"Failed to fetch profile: {err}") from err

        if res_json.get("status") != "success" or "data" not in res_json:
            raise RuntimeError(res_json.get("message", "Failed to fetch profile"))

        logger.info("Successfully fetched user profile for user_id: {}", res_json["data"].get("user_id", "unknown"))
        return res_json["data"]


# Alias for backward compatibility
ZerodhaAuthSession = ZerodhaAuthService
