"""Exponential moving average."""

import pandas as pd


def ema(values: pd.Series, period: int) -> pd.Series:
    """Return an exponential moving average."""

    if period < 1:
        raise ValueError("period must be positive")
    return values.ewm(span=period, adjust=False, min_periods=period).mean()
