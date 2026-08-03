"""Unit tests for PartitionedParquetStorage."""

from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from app.marketdata.storage import PartitionedParquetStorage


@pytest.fixture
def sample_df() -> pd.DataFrame:
    dates = pd.date_range("2024-01-15", periods=45, freq="D")
    return pd.DataFrame(
        {
            "open": [100.0 + i for i in range(45)],
            "high": [105.0 + i for i in range(45)],
            "low": [99.0 + i for i in range(45)],
            "close": [104.0 + i for i in range(45)],
            "volume": [1000.0 + i * 10 for i in range(45)],
        },
        index=dates,
    )


def test_save_and_load_partitioned(tmp_path: Path, sample_df: pd.DataFrame):
    storage = PartitionedParquetStorage(tmp_path)

    # Save partitioned data
    output_dir = storage.save(sample_df, "RELIANCE")
    assert output_dir.exists()
    assert (output_dir / "year=2024").exists()

    # Load back full range
    loaded = storage.load("RELIANCE")
    assert len(loaded) == 45
    assert list(loaded.columns) == ["open", "high", "low", "close", "volume"]

    # Load with date filtering
    filtered = storage.load("RELIANCE", start=date(2024, 1, 20), end=date(2024, 1, 25))
    assert len(filtered) == 6


def test_load_fallback_single_parquet_file(tmp_path: Path, sample_df: pd.DataFrame):
    storage = PartitionedParquetStorage(tmp_path)
    single_file = tmp_path / "tcs.parquet"
    sample_df.to_parquet(single_file)

    loaded = storage.load("TCS", start=date(2024, 1, 15), end=date(2024, 1, 20))
    assert len(loaded) == 6


def test_load_nonexistent_symbol(tmp_path: Path):
    storage = PartitionedParquetStorage(tmp_path)
    loaded = storage.load("UNKNOWN")
    assert loaded.empty
