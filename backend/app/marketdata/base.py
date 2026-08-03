"""Provider contract for historical OHLCV data."""

from abc import ABC, abstractmethod
from datetime import date

import pandas as pd


class MarketDataProvider(ABC):
    """All historical data sources return a normalized OHLCV DataFrame."""

    @abstractmethod
    async def get_candles(
        self, symbol: str, start: date, end: date, interval: str = "1d"
    ) -> pd.DataFrame:
        """Return timestamp-indexed open, high, low, close, volume candles."""
        pass
