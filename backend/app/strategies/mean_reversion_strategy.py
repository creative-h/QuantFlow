"""Bollinger Bands Mean Reversion strategy plugin."""

from typing import Optional, Union

import pandas as pd

from app.indicators.engine import IndicatorEngine
from app.models.dataclasses import Candle, Signal, SignalSide
from app.strategies.base import Strategy


class MeanReversionStrategy(Strategy):
    """Bollinger Bands mean-reversion strategy."""

    name = "mean_reversion"

    def __init__(self, period: int = 20, std_dev: float = 2.0) -> None:
        self.period = period
        self.std_dev = std_dev

    def initialize(self) -> None:
        """Initialize strategy state."""
        pass

    def compute_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Compute Bollinger Bands."""
        df = data.copy()
        df = IndicatorEngine.compute(
            df, indicator_type="bollinger", period=self.period, std_dev=self.std_dev
        )
        return df

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate mean reversion signals when close touches or pierces outer bands."""
        df = self.compute_indicators(data)
        close = df["close"]
        lower = df["bb_lower"]
        upper = df["bb_upper"]
        signals = pd.Series(index=df.index, data=0)

        signals[close <= lower] = 1
        signals[close >= upper] = -1
        return signals

    def generate_signal(
        self, data: Union[pd.DataFrame, list[Candle]]
    ) -> Union[Optional[Signal], int]:
        """Generate signal for BacktestEngine and StrategyEngine."""
        if isinstance(data, list):
            df = pd.DataFrame([c.to_dict() for c in data])
        else:
            df = data

        if len(df) < self.period:
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
