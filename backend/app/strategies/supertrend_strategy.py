"""Supertrend trend-following strategy plugin."""

from typing import Optional, Union

import pandas as pd

from app.indicators.engine import IndicatorEngine
from app.models.dataclasses import Candle, Signal, SignalSide
from app.strategies.base import Strategy


class SupertrendStrategy(Strategy):
    """Supertrend indicator trend-following strategy."""

    name = "supertrend"

    def __init__(self, period: int = 10, multiplier: float = 3.0) -> None:
        self.period = period
        self.multiplier = multiplier

    def initialize(self) -> None:
        """Initialize strategy indicators and state."""
        pass

    def compute_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Compute Supertrend indicator on OHLCV data."""
        df = data.copy()
        df = IndicatorEngine.compute(
            df,
            indicator_type="supertrend",
            period=self.period,
            multiplier=self.multiplier,
        )
        return df

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate signals based on Supertrend direction flips."""
        df = self.compute_indicators(data)
        direction = df["supertrend_dir"]
        signals = pd.Series(index=df.index, data=0)

        bullish = (direction == 1) & (direction.shift(1) == -1)
        bearish = (direction == -1) & (direction.shift(1) == 1)

        signals[bullish] = 1
        signals[bearish] = -1
        return signals

    def generate_signal(
        self, data: Union[pd.DataFrame, list[Candle]]
    ) -> Union[Optional[Signal], int]:
        """Generate signal for BacktestEngine and StrategyEngine."""
        if isinstance(data, list):
            df = pd.DataFrame([c.to_dict() for c in data])
        else:
            df = data

        if len(df) < self.period + 1:
            return 0

        signals = self.generate_signals(df)
        return int(signals.iloc[-1]) if not signals.empty else 0

    def on_candle(
        self, candle: Candle, history: Optional[pd.DataFrame] = None
    ) -> Optional[Signal]:
        """Receive latest candle event."""
        df = history if (history is not None and not history.empty) else pd.DataFrame([candle.to_dict()])
        sig_int = self.generate_signal(df)
        if sig_int == 1:
            return Signal(side=SignalSide.BUY, price=candle.close, confidence=0.8)
        elif sig_int == -1:
            return Signal(side=SignalSide.SELL, price=candle.close, confidence=0.8)
        return Signal(side=SignalSide.HOLD, price=candle.close, confidence=0.0)
