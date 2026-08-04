"""Provider contract for historical OHLCV data."""

from abc import ABC, abstractmethod
from datetime import date
from typing import Optional

import pandas as pd


class MarketDataProvider(ABC):
    """All historical data sources return a normalized OHLCV DataFrame."""

    @abstractmethod
    async def get_candles(
        self,
        symbol: str,
        start: Optional[date] = None,
        end: Optional[date] = None,
        period: Optional[str] = "1mo",
        interval: str = "1d",
    ) -> pd.DataFrame:
        """Return timestamp-indexed open, high, low, close, volume candles."""
        pass
