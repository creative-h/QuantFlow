"""Relative strength index."""

import pandas as pd


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Return Wilder's RSI, in the 0–100 range."""

    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    loss = -delta.clip(upper=0).ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    return 100 - (100 / (1 + gain / loss.replace(0, float("nan"))))
