"""Typed domain data objects for market candles and strategy signals."""

from dataclasses import asdict, dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any, Optional

import pandas as pd


class SignalSide(StrEnum):
    """Side of a trading signal."""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class Candle:
    """Normalized single OHLCV market candle."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

    @classmethod
    def from_series(cls, series: pd.Series, timestamp_name: Optional[str] = None) -> "Candle":
        """Construct Candle from a pandas Series or row."""
        ts = series.name if timestamp_name is None and isinstance(series.name, datetime) else series.get("timestamp", series.name)
        if isinstance(ts, str):
            ts = pd.to_datetime(ts).to_pydatetime()
        elif hasattr(ts, "to_pydatetime"):
            ts = ts.to_pydatetime()

        return cls(
            timestamp=ts,
            open=float(series["open"]),
            high=float(series["high"]),
            low=float(series["low"]),
            close=float(series["close"]),
            volume=float(series["volume"]),
        )

    def to_dict(self) -> dict[str, Any]:
        """Return dictionary representation."""
        res = asdict(self)
        if isinstance(self.timestamp, datetime):
            res["timestamp"] = self.timestamp.isoformat()
        return res


@dataclass
class Signal:
    """Strategy generated trading signal."""

    side: SignalSide
    price: float
    stop_loss: float = 0.0
    target: float = 0.0
    confidence: float = 1.0
    symbol: Optional[str] = None
    timestamp: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        """Return dictionary representation."""
        res = asdict(self)
        res["side"] = self.side.value
        if self.timestamp and isinstance(self.timestamp, datetime):
            res["timestamp"] = self.timestamp.isoformat()
        return res
