"""Unit tests for ResearchCache SQLite caching layer."""

import pandas as pd
import pytest

from app.research.caching import ResearchCache


@pytest.fixture
def temp_cache(tmp_path) -> ResearchCache:
    db_file = tmp_path / "test_cache.db"
    return ResearchCache(db_path=db_file)


def test_cache_dataframe_put_and_get(temp_cache: ResearchCache):
    df = pd.DataFrame({"close": [10.0, 20.0, 30.0], "volume": [100, 200, 300]})
    temp_cache.set_dataframe(df, "market_data", "AAPL", "1d")

    cached_df = temp_cache.get_dataframe("market_data", "AAPL", "1d")
    assert cached_df is not None
    assert len(cached_df) == 3
    assert list(cached_df["close"]) == [10.0, 20.0, 30.0]


def test_cache_dataframe_miss(temp_cache: ResearchCache):
    cached_df = temp_cache.get_dataframe("market_data", "NONEXISTENT", "1d")
    assert cached_df is None


def test_cache_result_dict_put_and_get(temp_cache: ResearchCache):
    res_dict = {"sharpe": 2.5, "net_profit": 1500.0, "params": {"fast": 5}}
    temp_cache.set_result(res_dict, "opt_result", "ema", "hash123")

    cached_res = temp_cache.get_result("opt_result", "ema", "hash123")
    assert cached_res is not None
    assert cached_res["sharpe"] == 2.5
    assert cached_res["params"]["fast"] == 5


def test_cache_clear(temp_cache: ResearchCache):
    df = pd.DataFrame({"close": [1.0]})
    temp_cache.set_dataframe(df, "prefix", "key1")
    temp_cache.set_result({"val": 1}, "prefix", "key2")

    temp_cache.clear()

    assert temp_cache.get_dataframe("prefix", "key1") is None
    assert temp_cache.get_result("prefix", "key2") is None
