"""Validation and normalization routines for OHLCV market data."""

import pandas as pd
from loguru import logger


class DataValidationError(ValueError):
    """Raised when market data fails validation constraints."""

    pass


REQUIRED_OHLCV_COLUMNS = ["open", "high", "low", "close", "volume"]


def normalize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize DataFrame to standard OHLCV schema with DatetimeIndex."""
    if df is None or df.empty:
        raise DataValidationError("Input DataFrame is empty")

    data = df.copy()

    # If MultiIndex columns (e.g. from yfinance download), flatten/select first level
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [col[0] for col in data.columns]

    # Convert column names to lowercase strings
    data.columns = [str(col).strip().lower() for col in data.columns]

    # Map common column aliases
    alias_map = {
        "adj close": "close",
        "vol": "volume",
        "trade_date": "timestamp",
        "date": "timestamp",
        "datetime": "timestamp",
        "time": "timestamp",
    }
    data = data.rename(columns=alias_map)

    # Ensure timestamp index
    if "timestamp" in data.columns:
        data["timestamp"] = pd.to_datetime(data["timestamp"])
        data = data.set_index("timestamp")

    if not isinstance(data.index, pd.DatetimeIndex):
        try:
            data.index = pd.to_datetime(data.index)
        except Exception as err:
            raise DataValidationError(f"Invalid timestamp index or format: {err}") from err

    data.index.name = "timestamp"

    # Check for missing required columns
    missing_cols = [col for col in REQUIRED_OHLCV_COLUMNS if col not in data.columns]
    if missing_cols:
        raise DataValidationError(f"Missing required OHLCV columns: {missing_cols}")

    # Select only OHLCV columns in canonical order
    data = data[REQUIRED_OHLCV_COLUMNS]

    # Cast numeric types
    for col in REQUIRED_OHLCV_COLUMNS:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    return data


def validate_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """Validate DataFrame against QuantFlow market data quality rules."""
    normalized = normalize_ohlcv(df)

    if normalized.empty:
        raise DataValidationError("OHLCV DataFrame is empty after normalization")

    # 1. Duplicate timestamps check
    if normalized.index.has_duplicates:
        duplicates = normalized.index[normalized.index.duplicated()].tolist()
        logger.error("Duplicate timestamps detected in market data: {}", duplicates[:5])
        raise DataValidationError(
            f"Duplicate timestamps detected: {len(duplicates)} duplicate entries found"
        )

    # 2. Sorted timestamp index check
    if not normalized.index.is_monotonic_increasing:
        normalized = normalized.sort_index()

    # 3. Timezone validation check
    if normalized.index.tz is not None:
        logger.debug("Market data timestamp index timezone: {}", normalized.index.tz)

    # 4. NaN / missing values check
    if normalized.isna().any().any():
        nan_counts = normalized.isna().sum().to_dict()
        logger.error("NaN values detected in market data: {}", nan_counts)
        raise DataValidationError(f"NaN values detected in market data: {nan_counts}")

    # 5. Negative price check (open, high, low, close must be >= 0)
    price_cols = ["open", "high", "low", "close"]
    for col in price_cols:
        if (normalized[col] < 0).any():
            invalid_rows = normalized[normalized[col] < 0]
            logger.error(
                "Negative prices detected in column {}: {} rows", col, len(invalid_rows)
            )
            raise DataValidationError(f"Negative price values detected in column '{col}'")

    # 6. Negative volume check (volume must be >= 0)
    if (normalized["volume"] < 0).any():
        logger.error("Negative volume detected")
        raise DataValidationError("Negative volume values detected")

    # 7. Logical OHLC consistency (high >= low)
    invalid_high_low = normalized[normalized["high"] < normalized["low"]]
    if not invalid_high_low.empty:
        logger.error("High price is less than Low price in {} rows", len(invalid_high_low))
        raise DataValidationError("Invalid candle: High price is less than Low price")

    logger.info("Market data validation passed successfully ({} candles)", len(normalized))
    return normalized
