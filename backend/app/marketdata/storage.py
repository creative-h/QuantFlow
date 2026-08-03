"""Partitioned Parquet storage manager for historical market data."""

from datetime import date
from pathlib import Path
from typing import Optional

import pandas as pd
from loguru import logger

from app.marketdata.validator import validate_ohlcv


class PartitionedParquetStorage:
    """Save and load OHLCV data partitioned by symbol, year, and month."""

    def __init__(self, base_dir: Path | str) -> None:
        self.base_dir = Path(base_dir)

    def save(self, df: pd.DataFrame, symbol: str) -> Path:
        """Save normalized OHLCV data partitioned by symbol and year/month."""
        validated_df = validate_ohlcv(df)
        data = validated_df.copy()

        data["symbol"] = symbol.upper()
        data["year"] = data.index.year
        data["month"] = data.index.month

        output_dir = self.base_dir / symbol.upper()
        output_dir.mkdir(parents=True, exist_ok=True)

        # Write partitioned parquet file(s)
        data.to_parquet(
            output_dir,
            partition_cols=["year", "month"],
            index=True,
        )
        logger.info("Saved partitioned Parquet market data for {} to {}", symbol, output_dir)
        return output_dir

    def load(
        self, symbol: str, start: Optional[date] = None, end: Optional[date] = None
    ) -> pd.DataFrame:
        """Load partitioned Parquet market data for a symbol and date range."""
        symbol_dir = self.base_dir / symbol.upper()

        if not symbol_dir.exists():
            # Fallback to single symbol file (symbol.parquet or SYMBOL.parquet)
            single_file = self.base_dir / f"{symbol.lower()}.parquet"
            if not single_file.exists():
                single_file = self.base_dir / f"{symbol.upper()}.parquet"
                if not single_file.exists():
                    logger.warning("No Parquet data found for symbol {}", symbol)
                    return pd.DataFrame()

            data = pd.read_parquet(single_file)
            data = validate_ohlcv(data)
        else:
            data = pd.read_parquet(symbol_dir)
            data = validate_ohlcv(data)

        if start:
            data = data.loc[data.index >= pd.to_datetime(start)]
        if end:
            # Include full end date
            end_ts = pd.to_datetime(end) + pd.Timedelta(hours=23, minutes=59, seconds=59)

            data = data.loc[data.index <= end_ts]

        return data.sort_index()
