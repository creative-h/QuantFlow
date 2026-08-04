"""CSV historical-data provider."""

from datetime import date
from pathlib import Path
from typing import Optional

import pandas as pd
from loguru import logger

from app.marketdata.base import MarketDataProvider
from app.marketdata.validator import validate_ohlcv


class CSVProvider(MarketDataProvider):
    """Read canonical OHLCV data from a CSV file per symbol with validation."""

    def __init__(self, directory: Path | str) -> None:
        self._directory = Path(directory)

    async def get_candles(
        self,
        symbol: str,
        start: Optional[date] = None,
        end: Optional[date] = None,
        period: Optional[str] = "1mo",
        interval: str = "1d",
    ) -> pd.DataFrame:
        """Load, filter, and validate OHLCV data from CSV."""
        path = self._directory / f"{symbol.lower()}.csv"
        if not path.exists():
            path = self._directory / f"{symbol.upper()}.csv"
            if not path.exists():
                logger.error("CSV file not found for symbol '{}' at {}", symbol, path)
                raise FileNotFoundError(f"CSV market data file not found for symbol '{symbol}'")

        logger.info("Reading CSV market data for '{}' from {}", symbol, path)
        data = pd.read_csv(path)
        validated = validate_ohlcv(data)

        if start is not None and end is not None:
            start_ts = pd.to_datetime(start)
            end_ts = pd.to_datetime(end) + pd.Timedelta(hours=23, minutes=59, seconds=59)
            filtered = validated.loc[(validated.index >= start_ts) & (validated.index <= end_ts)]
        else:
            filtered = validated

        if filtered.empty:
            logger.warning("CSV data for '{}' is empty after date range filtering", symbol)
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

        logger.info("Retrieved {} candles for '{}' from CSV", len(filtered), symbol)
        return filtered
