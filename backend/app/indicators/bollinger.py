"""Bollinger Bands indicator."""

import pandas as pd


def bollinger_bands(
    close: pd.Series, period: int = 20, std_dev: float = 2.0
) -> pd.DataFrame:
    """Return Upper, Middle (SMA), and Lower Bollinger Bands."""
    if period < 1:
        raise ValueError("period must be positive")

    middle = close.rolling(window=period, min_periods=period).mean()
    std = close.rolling(window=period, min_periods=period).std()

    upper = middle + (std_dev * std)
    lower = middle - (std_dev * std)

    return pd.DataFrame({"upper": upper, "middle": middle, "lower": lower})
