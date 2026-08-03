"""Unit tests for /auth/* API endpoints."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_zerodha_auth_service
from app.main import app
from app.services.zerodha_auth import ZerodhaAuthService


@pytest.fixture
def mock_auth_service():
    service = MagicMock(spec=ZerodhaAuthService)
    service.get_login_url.return_value = "https://kite.zerodha.com/connect/login?v=3&api_key=test"
    return service


@pytest.fixture
def client(mock_auth_service):
    app.dependency_overrides[get_zerodha_auth_service] = lambda: mock_auth_service
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_auth_login_endpoint(client: TestClient, mock_auth_service):
    response = client.get("/auth/login")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert "https://kite.zerodha.com/connect/login" in json_data["login_url"]


def test_auth_callback_missing_token(client: TestClient):
    response = client.get("/auth/callback")
    assert response.status_code == 400
    assert response.json()["detail"] == "Missing request_token parameter"


def test_auth_callback_failed_status(client: TestClient):
    response = client.get("/auth/callback?status=error")
    assert response.status_code == 401
    assert "Kite authentication was not successful" in response.json()["detail"]


def test_auth_callback_success(client: TestClient, mock_auth_service):
    mock_auth_service.exchange_token = AsyncMock(
        return_value={"user_id": "AB1234", "user_name": "Test User", "access_token": "token123"}
    )
    response = client.get("/auth/callback?request_token=valid_req_token")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert json_data["user_id"] == "AB1234"
    assert json_data["user_name"] == "Test User"


def test_auth_callback_exchange_error(client: TestClient, mock_auth_service):
    mock_auth_service.exchange_token = AsyncMock(side_effect=RuntimeError("Token exchange failed"))
    response = client.get("/auth/callback?request_token=invalid_req_token")
    assert response.status_code == 502
    assert "Unable to establish Kite session" in response.json()["detail"]


def test_auth_profile_unauthenticated(client: TestClient, mock_auth_service):
    mock_auth_service.get_profile = AsyncMock(
        side_effect=ValueError("No active Zerodha session found. Please log in.")
    )
    response = client.get("/auth/profile")
    assert response.status_code == 401
    assert "No active Zerodha session found" in response.json()["detail"]


def test_auth_profile_success(client: TestClient, mock_auth_service):
    mock_auth_service.get_profile = AsyncMock(
        return_value={"user_id": "AB1234", "user_name": "Test User", "email": "test@example.com"}
    )
    response = client.get("/auth/profile")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert json_data["data"]["user_id"] == "AB1234"


def test_auth_logout_success(client: TestClient, mock_auth_service):
    mock_auth_service.clear_session.return_value = True
    response = client.post("/auth/logout")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert json_data["message"] == "Logged out successfully"
