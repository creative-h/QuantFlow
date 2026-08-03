"""Long-only EMA crossover strategy."""

from typing import Optional

import pandas as pd

from app.indicators.engine import IndicatorEngine
from app.models.dataclasses import Candle, Signal, SignalSide
from app.models.trading import Order
from app.strategies.base import Strategy


class EMACrossoverStrategy(Strategy):
    """Buy when fast EMA crosses above slow EMA; exit on reverse crossover."""

    name = "ema"

    def __init__(self, fast_period: int = 9, slow_period: int = 21) -> None:
        if fast_period >= slow_period:
            raise ValueError("fast_period must be less than slow_period")
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.candle_history: list[Candle] = []
        self.position: int = 0

    def initialize(self) -> None:
        self.candle_history = []
        self.position = 0

    def on_candle(self, candle: Candle) -> Optional[Signal]:
        """Process incoming candle, append to history, and evaluate crossover."""
        self.candle_history.append(candle)
        return self.generate_signal(self.candle_history)

    def generate_signal(self, candles: list[Candle] | pd.DataFrame) -> Optional[Signal]:
        """Generate Signal based on fast/slow EMA crossover."""
        if isinstance(candles, list):
            if len(candles) < self.slow_period + 1:
                return Signal(side=SignalSide.HOLD, price=0.0)
            df = pd.DataFrame([c.to_dict() for c in candles])
        else:
            df = candles

        if len(df) < self.slow_period + 1:
            return Signal(side=SignalSide.HOLD, price=0.0)

        fast_series = IndicatorEngine.ema(df, self.fast_period)
        slow_series = IndicatorEngine.ema(df, self.slow_period)

        current_close = float(df["close"].iloc[-1])

        # Check Golden Cross (bullish)
        if (
            fast_series.iloc[-2] <= slow_series.iloc[-2]
            and fast_series.iloc[-1] > slow_series.iloc[-1]
        ):
            if self.position <= 0:
                self.position = 1
                return Signal(
                    side=SignalSide.BUY,
                    price=current_close,
                    stop_loss=current_close * 0.95,
                    target=current_close * 1.10,
                    confidence=0.8,
                )

        # Check Death Cross (bearish)
        elif (
            fast_series.iloc[-2] >= slow_series.iloc[-2]
            and fast_series.iloc[-1] < slow_series.iloc[-1]
        ):
            if self.position > 0:
                self.position = 0
                return Signal(
                    side=SignalSide.SELL,
                    price=current_close,
                    confidence=0.8,
                )

        return Signal(side=SignalSide.HOLD, price=current_close)

    def on_order(self, order: Order) -> None:
        """Callback when order fills or updates."""
        pass
