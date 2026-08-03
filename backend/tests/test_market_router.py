"""Unit tests for /market/history API router."""

from datetime import date
from unittest.mock import AsyncMock, patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_df() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    return pd.DataFrame(
        {
            "open": [100.0, 101.0, 102.0],
            "high": [105.0, 106.0, 107.0],
            "low": [99.0, 100.0, 101.0],
            "close": [104.0, 105.0, 106.0],
            "volume": [1000.0, 1100.0, 1200.0],
        },
        index=dates,
    )


def test_get_market_history_yfinance_success(client: TestClient, sample_df: pd.DataFrame):
    with patch(
        "app.marketdata.yfinance_provider.YahooFinanceProvider.get_candles",
        new_callable=AsyncMock,
        return_value=sample_df,
    ):
        response = client.get(
            "/market/history?symbol=AAPL&start=2024-01-01&end=2024-01-03&provider=yfinance"
        )
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["status"] == "success"
        assert json_data["symbol"] == "AAPL"
        assert json_data["count"] == 3
        assert len(json_data["data"]) == 3
        assert json_data["data"][0]["close"] == 104.0


def test_get_market_history_invalid_date_range(client: TestClient):
    response = client.get(
        "/market/history?symbol=AAPL&start=2024-01-10&end=2024-01-01&provider=yfinance"
    )
    assert response.status_code == 400
    assert "Invalid date range" in response.json()["detail"]


def test_get_market_history_unsupported_provider(client: TestClient):
    response = client.get(
        "/market/history?symbol=AAPL&start=2024-01-01&end=2024-01-03&provider=invalid_provider"
    )
    assert response.status_code == 400
    assert "Unsupported market data provider" in response.json()["detail"]


def test_get_market_history_file_not_found(client: TestClient):
    with patch(
        "app.marketdata.csv_provider.CSVProvider.get_candles",
        new_callable=AsyncMock,
        side_effect=FileNotFoundError("CSV file not found"),
    ):
        response = client.get(
            "/market/history?symbol=NONEXISTENT&start=2024-01-01&end=2024-01-03&provider=csv"
        )
        assert response.status_code == 404
        assert "Market data not found" in response.json()["detail"]


def test_get_market_history_validation_error(client: TestClient):
    from app.marketdata.validator import DataValidationError

    with patch(
        "app.marketdata.yfinance_provider.YahooFinanceProvider.get_candles",
        new_callable=AsyncMock,
        side_effect=DataValidationError("Negative price values detected"),
    ):
        response = client.get(
            "/market/history?symbol=BADSYMBOL&start=2024-01-01&end=2024-01-03&provider=yfinance"
        )
        assert response.status_code == 400
        assert "Data validation failed" in response.json()["detail"]


def test_get_market_history_upstream_error(client: TestClient):
    with patch(
        "app.marketdata.yfinance_provider.YahooFinanceProvider.get_candles",
        new_callable=AsyncMock,
        side_effect=RuntimeError("Yahoo API connection timeout"),
    ):
        response = client.get(
            "/market/history?symbol=TIMEOUT&start=2024-01-01&end=2024-01-03&provider=yfinance"
        )
        assert response.status_code == 502
        assert "Failed to fetch market data" in response.json()["detail"]


def test_get_market_history_save_parquet_option(client: TestClient, sample_df: pd.DataFrame):
    with patch(
        "app.marketdata.yfinance_provider.YahooFinanceProvider.get_candles",
        new_callable=AsyncMock,
        return_value=sample_df,
    ), patch(
        "app.marketdata.storage.PartitionedParquetStorage.save"
    ) as mock_save:
        response = client.get(
            "/market/history?symbol=AAPL&start=2024-01-01&end=2024-01-03&provider=yfinance&save_parquet=true"
        )
        assert response.status_code == 200
        mock_save.assert_called_once()
