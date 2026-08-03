"""Unit tests for ZerodhaAuthService."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.core.config import Settings
from app.services.zerodha_auth import ZerodhaAuthService


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        secret_key="test-secret-key-must-be-32-chars-long-or-more",
        zerodha_api_key="test_api_key",
        zerodha_api_secret="test_api_secret",
        zerodha_redirect_url="https://localhost:8000/auth/callback",
    )


@pytest.fixture
def temp_session_file(tmp_path: Path) -> Path:
    return tmp_path / "data" / "session.json"


def test_get_login_url(test_settings: Settings, temp_session_file: Path):
    service = ZerodhaAuthService(settings=test_settings, session_file=temp_session_file)
    url = service.get_login_url()
    assert "https://kite.zerodha.com/connect/login" in url
    assert "api_key=test_api_key" in url
    assert "redirect_url=https%3A%2F%2Flocalhost%3A8000%2Fauth%2Fcallback" in url or "redirect_url=" in url


def test_save_load_clear_session(test_settings: Settings, temp_session_file: Path):
    service = ZerodhaAuthService(settings=test_settings, session_file=temp_session_file)

    # Initial state: no session
    assert service.load_session() is None

    # Save session
    session_payload = {"user_id": "AB1234", "access_token": "mock_access_token_123"}
    service.save_session(session_payload)

    assert temp_session_file.exists()

    # Load session
    loaded = service.load_session()
    assert loaded == session_payload

    # Clear session
    assert service.clear_session() is True
    assert service.load_session() is None


@pytest.mark.asyncio
async def test_exchange_token_success(test_settings: Settings, temp_session_file: Path):
    mock_client = MagicMock(spec=httpx.AsyncClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "status": "success",
        "data": {
            "user_id": "AB1234",
            "user_name": "John Doe",
            "access_token": "secret_access_token",
            "public_token": "secret_public_token",
        },
    }
    mock_client.post = AsyncMock(return_value=mock_response)

    service = ZerodhaAuthService(
        settings=test_settings, session_file=temp_session_file, client=mock_client
    )
    result = await service.exchange_token("mock_request_token")

    assert result["user_id"] == "AB1234"
    assert result["access_token"] == "secret_access_token"

    # Verify session was saved to file
    with open(temp_session_file, "r", encoding="utf-8") as f:
        saved_data = json.load(f)
    assert saved_data["user_id"] == "AB1234"


@pytest.mark.asyncio
async def test_exchange_token_failure(test_settings: Settings, temp_session_file: Path):
    mock_client = MagicMock(spec=httpx.AsyncClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 400
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Bad Request", request=MagicMock(), response=mock_response
    )
    mock_response.json.return_value = {"status": "error", "message": "Invalid checksum"}
    mock_client.post = AsyncMock(return_value=mock_response)

    service = ZerodhaAuthService(
        settings=test_settings, session_file=temp_session_file, client=mock_client
    )

    with pytest.raises(RuntimeError, match="Invalid checksum"):
        await service.exchange_token("bad_request_token")


@pytest.mark.asyncio
async def test_get_profile_unauthenticated(test_settings: Settings, temp_session_file: Path):
    service = ZerodhaAuthService(settings=test_settings, session_file=temp_session_file)
    with pytest.raises(ValueError, match="No active Zerodha session found"):
        await service.get_profile()


@pytest.mark.asyncio
async def test_get_profile_success(test_settings: Settings, temp_session_file: Path):
    mock_client = MagicMock(spec=httpx.AsyncClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "status": "success",
        "data": {
            "user_id": "AB1234",
            "user_name": "Jane Doe",
            "email": "jane@example.com",
            "user_type": "individual",
        },
    }
    mock_client.get = AsyncMock(return_value=mock_response)

    service = ZerodhaAuthService(
        settings=test_settings, session_file=temp_session_file, client=mock_client
    )
    # Save a valid session first
    service.save_session({"user_id": "AB1234", "access_token": "valid_token"})

    profile = await service.get_profile()
    assert profile["user_id"] == "AB1234"
    assert profile["user_name"] == "Jane Doe"
