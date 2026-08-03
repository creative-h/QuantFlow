"""Volume-weighted average price."""

import pandas as pd


def vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
    """Return cumulative session VWAP for the supplied candles."""

    typical_price = (high + low + close) / 3
    return (typical_price * volume).cumsum() / volume.cumsum().replace(0, float("nan"))
