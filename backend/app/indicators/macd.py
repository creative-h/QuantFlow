"""Moving average convergence-divergence."""

import pandas as pd

from app.indicators.ema import ema


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """Return MACD line, signal line, and histogram."""

    line = ema(close, fast) - ema(close, slow)
    signal_line = ema(line, signal)
    return pd.DataFrame({"macd": line, "signal": signal_line, "histogram": line - signal_line})
