"""VWAP mean-reversion strategy."""

import pandas as pd

from app.indicators.vwap import vwap
from app.strategies.base import Strategy


class VWAPReversalStrategy(Strategy):
    """Enter when price crosses VWAP and exit on a crossing in the other direction."""

    def initialize(self) -> None:
        return None

    def generate_signal(self, data: pd.DataFrame) -> int:
        if len(data) < 2:
            return 0
        line = vwap(data["high"], data["low"], data["close"], data["volume"])
        if data["close"].iloc[-2] <= line.iloc[-2] and data["close"].iloc[-1] > line.iloc[-1]:
            return 1
        if data["close"].iloc[-2] >= line.iloc[-2] and data["close"].iloc[-1] < line.iloc[-1]:
            return -1
        return 0
