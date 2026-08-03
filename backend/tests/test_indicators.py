import pandas as pd

from app.indicators.ema import ema
from app.indicators.rsi import rsi


def test_ema_returns_series_with_warmup() -> None:
    values = pd.Series([1.0, 2.0, 3.0, 4.0])
    result = ema(values, period=2)
    assert result.iloc[0] != result.iloc[0]
    assert result.iloc[-1] > result.iloc[-2]


def test_rsi_is_bounded() -> None:
    result = rsi(pd.Series(range(1, 30)), period=14).dropna()
    assert result.between(0, 100).all()
