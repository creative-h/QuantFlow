"""Unit tests for thread-safe TickCache and latency calculation."""

from datetime import datetime, timedelta
import time

import pytest

from app.marketdata.live_feed import Tick
from app.marketdata.tick_cache import CachedTickEntry, TickCache


def test_tick_cache_initialization():
    cache = TickCache()
    assert cache.get_latest("NIFTY") is None
    assert cache.get_previous("NIFTY") is None
    assert cache.get_latency_ms("NIFTY") == 0.0


def test_tick_cache_update_tick_latest_and_previous():
    cache = TickCache()
    now = datetime.now()

    tick1 = Tick(symbol="NIFTY", price=24900.0, volume=100, timestamp=now)
    cache.update_tick(tick1)

    assert cache.get_latest("NIFTY") == tick1
    assert cache.get_previous("NIFTY") is None

    tick2 = Tick(symbol="NIFTY", price=24915.0, volume=150, timestamp=now)
    cache.update_tick(tick2)

    assert cache.get_latest("NIFTY") == tick2
    assert cache.get_previous("NIFTY") == tick1


def test_tick_cache_latency_calculation():
    cache = TickCache()
    past_ts = datetime.now() - timedelta(milliseconds=250)
    tick = Tick(symbol="BANKNIFTY", price=55000.0, volume=500, timestamp=past_ts)
    cache.update_tick(tick)

    latency = cache.get_latency_ms("BANKNIFTY")
    assert latency >= 200.0


def test_tick_cache_get_all_latest():
    cache = TickCache()
    cache.update_tick(Tick(symbol="NIFTY", price=24900.0, volume=100))
    cache.update_tick(Tick(symbol="BANKNIFTY", price=55000.0, volume=200))

    all_latest = cache.get_all_latest()
    assert "NIFTY" in all_latest
    assert "BANKNIFTY" in all_latest
    assert all_latest["NIFTY"].price == 24900.0


def test_cached_tick_entry_dataclass():
    entry = CachedTickEntry(symbol="FINNIFTY", latency_ms=15.5)
    assert entry.symbol == "FINNIFTY"
    assert entry.latency_ms == 15.5
