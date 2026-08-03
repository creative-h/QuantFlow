"""Unit tests for market data validator and normalizer."""

import pandas as pd
import pytest

from app.marketdata.validator import (
    DataValidationError,
    normalize_ohlcv,
    validate_ohlcv,
)


def create_sample_ohlcv() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=5, freq="D")
    return pd.DataFrame(
        {
            "Open": [100.0, 101.0, 102.0, 103.0, 104.0],
            "High": [105.0, 106.0, 107.0, 108.0, 109.0],
            "Low": [99.0, 100.0, 101.0, 102.0, 103.0],
            "Close": [104.0, 105.0, 106.0, 107.0, 108.0],
            "Volume": [1000, 1100, 1200, 1300, 1400],
        },
        index=dates,
    )


def test_normalize_ohlcv_success():
    df = create_sample_ohlcv()
    norm = normalize_ohlcv(df)
    assert list(norm.columns) == ["open", "high", "low", "close", "volume"]
    assert isinstance(norm.index, pd.DatetimeIndex)
    assert norm.index.name == "timestamp"


def test_normalize_ohlcv_multiindex_and_aliases():
    dates = pd.date_range("2024-01-01", periods=2, freq="D")
    df = pd.DataFrame(
        {
            "open": [10.0, 20.0],
            "high": [12.0, 22.0],
            "low": [9.0, 19.0],
            "adj close": [11.0, 21.0],
            "vol": [500, 600],
            "date": dates,
        }
    )
    norm = normalize_ohlcv(df)
    assert "close" in norm.columns
    assert "volume" in norm.columns


def test_normalize_ohlcv_empty():
    with pytest.raises(DataValidationError, match="Input DataFrame is empty"):
        normalize_ohlcv(pd.DataFrame())


def test_normalize_ohlcv_missing_columns():
    df = pd.DataFrame({"open": [10.0], "high": [12.0]}, index=pd.date_range("2024-01-01", periods=1))
    with pytest.raises(DataValidationError, match="Missing required OHLCV columns"):
        normalize_ohlcv(df)


def test_validate_ohlcv_valid():
    df = create_sample_ohlcv()
    validated = validate_ohlcv(df)
    assert len(validated) == 5


def test_validate_ohlcv_duplicate_timestamps():
    dates = pd.to_datetime(["2024-01-01", "2024-01-01", "2024-01-02"])
    df = pd.DataFrame(
        {
            "open": [10.0, 11.0, 12.0],
            "high": [15.0, 15.0, 15.0],
            "low": [9.0, 9.0, 9.0],
            "close": [14.0, 14.0, 14.0],
            "volume": [100, 100, 100],
        },
        index=dates,
    )
    with pytest.raises(DataValidationError, match="Duplicate timestamps detected"):
        validate_ohlcv(df)


def test_validate_ohlcv_nan_values():
    df = create_sample_ohlcv()
    df.iloc[2, 0] = None  # Introduce NaN
    with pytest.raises(DataValidationError, match="NaN values detected"):
        validate_ohlcv(df)


def test_validate_ohlcv_negative_prices():
    df = create_sample_ohlcv()
    df.iloc[1, 3] = -10.0  # Negative close price
    with pytest.raises(DataValidationError, match="Negative price values detected"):
        validate_ohlcv(df)


def test_validate_ohlcv_negative_volume():
    df = create_sample_ohlcv()
    df.iloc[0, 4] = -500  # Negative volume
    with pytest.raises(DataValidationError, match="Negative volume values detected"):
        validate_ohlcv(df)


def test_validate_ohlcv_invalid_high_low():
    df = create_sample_ohlcv()
    df.iloc[0, 1] = 90.0  # High lower than Low (99.0)
    with pytest.raises(DataValidationError, match="High price is less than Low price"):
        validate_ohlcv(df)
