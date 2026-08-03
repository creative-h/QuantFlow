"""Parquet historical-data provider."""

from datetime import date
from pathlib import Path

import pandas as pd
from loguru import logger

from app.marketdata.base import MarketDataProvider
from app.marketdata.storage import PartitionedParquetStorage


class ParquetProvider(MarketDataProvider):
    """Read canonical OHLCV data from Parquet files per symbol."""

    def __init__(self, directory: Path | str) -> None:
        self._storage = PartitionedParquetStorage(directory)
        self._directory = Path(directory)

    async def get_candles(
        self, symbol: str, start: date, end: date, interval: str = "1d"
    ) -> pd.DataFrame:
        """Load, filter, and validate OHLCV data from Parquet."""
        logger.info("Reading Parquet market data for '{}' from {}", symbol, self._directory)
        data = self._storage.load(symbol, start=start, end=end)
        if data.empty:
            logger.warning("No Parquet candles found for '{}' in date range", symbol)
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

        logger.info("Retrieved {} candles for '{}' from Parquet", len(data), symbol)
        return data
