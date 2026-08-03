"""NSE bhavcopy historical-data provider."""

from datetime import date
from pathlib import Path

import pandas as pd

from app.marketdata.base import MarketDataProvider


class NSEBhavcopyProvider(MarketDataProvider):
    """Load downloaded NSE bhavcopy CSV files from local storage."""

    def __init__(self, directory: Path) -> None:
        self._directory = directory

    async def get_candles(self, symbol: str, start: date, end: date) -> pd.DataFrame:
        files = sorted(self._directory.glob("*.csv"))
        frames = [pd.read_csv(file) for file in files]
        if not frames:
            raise FileNotFoundError("No bhavcopy CSV files were found")
        data = pd.concat(frames, ignore_index=True)
        data.columns = data.columns.str.upper()
        rows = data.loc[data["SYMBOL"] == symbol].copy()
        rows["timestamp"] = pd.to_datetime(rows["TIMESTAMP"])
        rows = rows.set_index("timestamp").sort_index().loc[str(start):str(end)]
        return pd.DataFrame({"open": rows["OPEN"], "high": rows["HIGH"], "low": rows["LOW"], "close": rows["CLOSE"], "volume": rows["TOTTRDQTY"]})
