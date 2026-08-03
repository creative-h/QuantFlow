"""Average Directional Index (ADX)."""

import numpy as np
import pandas as pd


def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.DataFrame:
    """Return ADX line, +DI, and -DI."""
    up = high.diff()
    down = -low.diff()

    plus_dm = pd.Series(np.where((up > down) & (up > 0), up, 0.0), index=high.index)
    minus_dm = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=high.index)

    tr = pd.concat(
        [high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1
    ).max(axis=1)

    atr_val = tr.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    plus_di = 100 * (
        plus_dm.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
        / atr_val.replace(0, float("nan"))
    )
    minus_di = 100 * (
        minus_dm.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
        / atr_val.replace(0, float("nan"))
    )

    dx = (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, float("nan")) * 100
    adx_val = dx.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()

    return pd.DataFrame({"adx": adx_val, "plus_di": plus_di, "minus_di": minus_di})
