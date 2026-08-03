"""Unit tests for Market Data Providers."""

from datetime import date
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from app.marketdata.csv_provider import CSVProvider
from app.marketdata.parquet_provider import ParquetProvider
from app.marketdata.yfinance_provider import YahooFinanceProvider


@pytest.fixture
def sample_df() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=5, freq="D")
    return pd.DataFrame(
        {
            "open": [100.0, 101.0, 102.0, 103.0, 104.0],
            "high": [105.0, 106.0, 107.0, 108.0, 109.0],
            "low": [99.0, 100.0, 101.0, 102.0, 103.0],
            "close": [104.0, 105.0, 106.0, 107.0, 108.0],
            "volume": [1000.0, 1100.0, 1200.0, 1300.0, 1400.0],
        },
        index=dates,
    )


# --- YahooFinanceProvider Tests ---


@pytest.mark.asyncio
async def test_yfinance_provider_success(sample_df: pd.DataFrame):
    provider = YahooFinanceProvider(max_retries=2, retry_delay=0.01)

    with patch("yfinance.download", return_value=sample_df):
        candles = await provider.get_candles(
            "AAPL", start=date(2024, 1, 1), end=date(2024, 1, 5)
        )
        assert len(candles) == 5
        assert list(candles.columns) == ["open", "high", "low", "close", "volume"]


@pytest.mark.asyncio
async def test_yfinance_provider_retry_recovery(sample_df: pd.DataFrame):
    provider = YahooFinanceProvider(max_retries=3, retry_delay=0.01)
    side_effects = [Exception("Network error"), sample_df]

    with patch("yfinance.download", side_effect=side_effects):
        candles = await provider.get_candles(
            "AAPL", start=date(2024, 1, 1), end=date(2024, 1, 5)
        )
        assert len(candles) == 5


@pytest.mark.asyncio
async def test_yfinance_provider_exhaust_retries():
    provider = YahooFinanceProvider(max_retries=2, retry_delay=0.01)

    with patch("yfinance.download", side_effect=Exception("API down")):
        with pytest.raises(RuntimeError, match="Failed to fetch market data"):
            await provider.get_candles(
                "INVALID", start=date(2024, 1, 1), end=date(2024, 1, 5)
            )


# --- CSVProvider Tests ---


@pytest.mark.asyncio
async def test_csv_provider_success(tmp_path: Path, sample_df: pd.DataFrame):
    csv_file = tmp_path / "aapl.csv"
    sample_df.reset_index(names="timestamp").to_csv(csv_file, index=False)

    provider = CSVProvider(directory=tmp_path)
    candles = await provider.get_candles(
        "AAPL", start=date(2024, 1, 2), end=date(2024, 1, 4)
    )
    assert len(candles) == 3


@pytest.mark.asyncio
async def test_csv_provider_missing_file(tmp_path: Path):
    provider = CSVProvider(directory=tmp_path)
    with pytest.raises(FileNotFoundError, match="CSV market data file not found"):
        await provider.get_candles(
            "NONEXISTENT", start=date(2024, 1, 1), end=date(2024, 1, 5)
        )


@pytest.mark.asyncio
async def test_csv_provider_empty_date_range(tmp_path: Path, sample_df: pd.DataFrame):
    csv_file = tmp_path / "aapl.csv"
    sample_df.reset_index(names="timestamp").to_csv(csv_file, index=False)

    provider = CSVProvider(directory=tmp_path)
    candles = await provider.get_candles(
        "AAPL", start=date(2025, 1, 1), end=date(2025, 1, 5)
    )
    assert candles.empty


# --- ParquetProvider Tests ---


@pytest.mark.asyncio
async def test_parquet_provider_success(tmp_path: Path, sample_df: pd.DataFrame):
    parquet_file = tmp_path / "aapl.parquet"
    sample_df.to_parquet(parquet_file)

    provider = ParquetProvider(directory=tmp_path)
    candles = await provider.get_candles(
        "AAPL", start=date(2024, 1, 1), end=date(2024, 1, 3)
    )
    assert len(candles) == 3


@pytest.mark.asyncio
async def test_parquet_provider_missing_data(tmp_path: Path):
    provider = ParquetProvider(directory=tmp_path)
    candles = await provider.get_candles(
        "NONEXISTENT", start=date(2024, 1, 1), end=date(2024, 1, 5)
    )
    assert candles.empty
