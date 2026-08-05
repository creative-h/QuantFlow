"""Unit tests for real-time CandleBuilder aggregation."""

from datetime import datetime, timedelta

import pandas as pd
import pytest

from app.marketdata.candle_builder import CandleBuilder
from app.marketdata.live_feed import Tick
from app.models.dataclasses import Candle


def test_candle_builder_process_tick():
    builder = CandleBuilder()
    now = datetime(2024, 1, 1, 10, 0, 0)

    tick1 = Tick(symbol="NIFTY", price=24900.0, volume=100, timestamp=now)
    builder.process_tick(tick1)

    # Initial tick creates current candle
    current = builder._current_candles["NIFTY"]["1m"]
    assert current["open"] == 24900.0
    assert current["high"] == 24900.0
    assert current["low"] == 24900.0
    assert current["close"] == 24900.0
    assert current["volume"] == 100


def test_candle_builder_tick_updates_high_low_close():
    builder = CandleBuilder()
    now = datetime(2024, 1, 1, 10, 0, 0)

    builder.process_tick(Tick(symbol="NIFTY", price=24900.0, volume=100, timestamp=now))
    builder.process_tick(Tick(symbol="NIFTY", price=24925.0, volume=150, timestamp=now))
    builder.process_tick(Tick(symbol="NIFTY", price=24880.0, volume=200, timestamp=now))

    current = builder._current_candles["NIFTY"]["1m"]
    assert current["open"] == 24900.0
    assert current["high"] == 24925.0
    assert current["low"] == 24880.0
    assert current["close"] == 24880.0
    assert current["volume"] == 450


def test_candle_builder_completed_bar_emission():
    emitted = []

    def on_candle(symbol, timeframe, candle):
        emitted.append((symbol, timeframe, candle))

    builder = CandleBuilder()
    builder.register_listener(on_candle)

    # Tick 1
    ts1 = datetime(2024, 1, 1, 10, 0, 10)
    builder.process_tick(Tick(symbol="NIFTY", price=24900.0, volume=100, timestamp=ts1))

    # Tick 2 in next minute boundary
    ts2 = datetime(2024, 1, 1, 10, 1, 10)
    builder.process_tick(Tick(symbol="NIFTY", price=24910.0, volume=120, timestamp=ts2))

    assert len(emitted) > 0
    sym, tf, candle = emitted[0]
    assert sym == "NIFTY"
    assert tf == "1m"
    assert candle.open == 24900.0
    assert candle.close == 24900.0


def test_candle_builder_get_candle_dataframe():
    builder = CandleBuilder()
    ts1 = datetime(2024, 1, 1, 10, 0, 10)
    builder.process_tick(Tick(symbol="BANKNIFTY", price=55000.0, volume=100, timestamp=ts1))

    ts2 = datetime(2024, 1, 1, 10, 1, 10)
    builder.process_tick(Tick(symbol="BANKNIFTY", price=55050.0, volume=150, timestamp=ts2))

    df = builder.get_candle_dataframe("BANKNIFTY", "1m")
    assert isinstance(df, pd.DataFrame)
    assert len(df) >= 1
    assert "close" in df.columns
