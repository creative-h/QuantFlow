"""Opening Range Breakout (ORB) strategy plugin."""

from typing import Optional, Union

import pandas as pd

from app.models.dataclasses import Candle, Signal, SignalSide
from app.strategies.base import Strategy


class ORBStrategy(Strategy):
    """Opening Range Breakout strategy trading breakouts above/below initial session range."""

    name = "orb"

    def __init__(self, breakout_candles: int = 5) -> None:
        self.breakout_candles = breakout_candles

    def initialize(self) -> None:
        """Initialize strategy state."""
        pass

    def compute_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Compute opening high/low levels over initial N candles."""
        df = data.copy()
        if len(df) >= self.breakout_candles:
            orb_high = df["high"].iloc[: self.breakout_candles].max()
            orb_low = df["low"].iloc[: self.breakout_candles].min()
        else:
            orb_high = df["high"].max() if not df.empty else 0.0
            orb_low = df["low"].min() if not df.empty else 0.0

        df["orb_high"] = orb_high
        df["orb_low"] = orb_low
        return df

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate signals when price breaks above ORB High or below ORB Low."""
        df = self.compute_indicators(data)
        signals = pd.Series(index=df.index, data=0)

        if len(df) <= self.breakout_candles:
            return signals

        close = df["close"]
        orb_high = df["orb_high"]
        orb_low = df["orb_low"]

        bullish = (close > orb_high) & (close.shift(1) <= orb_high)
        bearish = (close < orb_low) & (close.shift(1) >= orb_low)

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

        if len(df) <= self.breakout_candles:
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
            return Signal(side=SignalSide.BUY, price=candle.close, confidence=0.85)
        elif sig_int == -1:
            return Signal(side=SignalSide.SELL, price=candle.close, confidence=0.85)
        return Signal(side=SignalSide.HOLD, price=candle.close, confidence=0.0)
