"""VWAP mean-reversion strategy plugin."""

from typing import Optional, Union

import pandas as pd

from app.indicators.engine import IndicatorEngine
from app.models.dataclasses import Candle, Signal, SignalSide
from app.strategies.base import Strategy


class VWAPStrategy(Strategy):
    """VWAP mean-reversion strategy trading price deviations from VWAP."""

    name = "vwap"

    def __init__(self, deviation_pct: float = 1.5) -> None:
        self.deviation_pct = deviation_pct

    def initialize(self) -> None:
        """Initialize strategy state."""
        pass

    def compute_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Compute VWAP indicator."""
        df = data.copy()
        df = IndicatorEngine.compute(df, indicator_type="vwap")
        return df

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate signals when close deviates significantly from VWAP."""
        df = self.compute_indicators(data)
        vwap = df["vwap"]
        close = df["close"]
        signals = pd.Series(index=df.index, data=0)

        lower_bound = vwap * (1.0 - self.deviation_pct / 100.0)
        upper_bound = vwap * (1.0 + self.deviation_pct / 100.0)

        signals[close < lower_bound] = 1
        signals[close > upper_bound] = -1
        return signals

    def generate_signal(
        self, data: Union[pd.DataFrame, list[Candle]]
    ) -> Union[Optional[Signal], int]:
        """Generate signal for BacktestEngine and StrategyEngine."""
        if isinstance(data, list):
            df = pd.DataFrame([c.to_dict() for c in data])
        else:
            df = data

        if df.empty:
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
            return Signal(side=SignalSide.BUY, price=candle.close, confidence=0.75)
        elif sig_int == -1:
            return Signal(side=SignalSide.SELL, price=candle.close, confidence=0.75)
        return Signal(side=SignalSide.HOLD, price=candle.close, confidence=0.0)
