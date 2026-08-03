"""RSI Pullback strategy plugin."""

from typing import Optional, Union

import pandas as pd

from app.indicators.engine import IndicatorEngine
from app.models.dataclasses import Candle, Signal, SignalSide
from app.strategies.base import Strategy


class RSIPullbackStrategy(Strategy):
    """RSI Overbought / Oversold pullback strategy."""

    name = "rsi"

    def __init__(
        self, period: int = 14, oversold: float = 30.0, overbought: float = 70.0
    ) -> None:
        self.period = period
        self.oversold = oversold
        self.overbought = overbought

    def initialize(self) -> None:
        """Initialize strategy state."""
        pass

    def compute_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Compute RSI indicator."""
        df = data.copy()
        df = IndicatorEngine.compute(df, indicator_type="rsi", period=self.period)
        return df

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate signals on RSI crossing thresholds."""
        df = self.compute_indicators(data)
        rsi = df["rsi"]
        signals = pd.Series(index=df.index, data=0)

        buy_cond = (rsi > self.oversold) & (rsi.shift(1) <= self.oversold)
        sell_cond = (rsi < self.overbought) & (rsi.shift(1) >= self.overbought)

        signals[buy_cond] = 1
        signals[sell_cond] = -1
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
