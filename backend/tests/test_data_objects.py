"""Unit tests for typed domain data objects (Candle, Signal, SignalSide)."""

from datetime import datetime

import pandas as pd
import pytest

from app.models.dataclasses import Candle, Signal, SignalSide


def test_candle_creation_and_to_dict():
    now = datetime(2024, 1, 15, 10, 30)
    candle = Candle(timestamp=now, open=100.0, high=105.0, low=98.0, close=104.0, volume=1000.0)

    assert candle.open == 100.0
    assert candle.high == 105.0
    assert candle.low == 98.0
    assert candle.close == 104.0
    assert candle.volume == 1000.0

    d = candle.to_dict()
    assert d["timestamp"] == now.isoformat()
    assert d["close"] == 104.0


def test_candle_from_series():
    series = pd.Series(
        {"open": 50.0, "high": 55.0, "low": 48.0, "close": 54.0, "volume": 500.0},
        name=pd.Timestamp("2024-02-01 09:15:00"),
    )
    candle = Candle.from_series(series)
    assert candle.open == 50.0
    assert candle.close == 54.0
    assert candle.timestamp == datetime(2024, 2, 1, 9, 15)


def test_signal_creation_and_to_dict():
    now = datetime(2024, 1, 15, 10, 30)
    sig = Signal(
        side=SignalSide.BUY,
        price=150.0,
        stop_loss=145.0,
        target=165.0,
        confidence=0.9,
        symbol="AAPL",
        timestamp=now,
    )

    assert sig.side == SignalSide.BUY
    assert sig.price == 150.0
    assert sig.stop_loss == 145.0
    assert sig.target == 165.0
    assert sig.confidence == 0.9

    d = sig.to_dict()
    assert d["side"] == "BUY"
    assert d["price"] == 150.0
    assert d["timestamp"] == now.isoformat()
