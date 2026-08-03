"""Unit tests for plugin strategies (Supertrend, VWAP, RSI, ORB, Mean Reversion)."""

from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from app.models.dataclasses import Candle, SignalSide
from app.strategies.mean_reversion_strategy import MeanReversionStrategy
from app.strategies.orb_strategy import ORBStrategy
from app.strategies.rsi_strategy import RSIPullbackStrategy
from app.strategies.supertrend_strategy import SupertrendStrategy
from app.strategies.vwap_strategy import VWAPStrategy


@pytest.fixture
def sample_data() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=30, freq="D")
    np.random.seed(42)
    close = 100.0 + np.cumsum(np.random.randn(30))
    open_p = close - 0.5
    high = np.maximum(open_p, close) + 1.0
    low = np.minimum(open_p, close) - 1.0
    volume = np.random.randint(1000, 5000, size=30)
    return pd.DataFrame(
        {"open": open_p, "high": high, "low": low, "close": close, "volume": volume},
        index=dates,
    )


def test_supertrend_strategy(sample_data: pd.DataFrame):
    strat = SupertrendStrategy(period=7, multiplier=3.0)
    signals = strat.generate_signals(sample_data)
    assert isinstance(signals, pd.Series)
    assert len(signals) == len(sample_data)

    candle = Candle(
        timestamp=datetime.now(),
        open=100.0,
        high=102.0,
        low=99.0,
        close=101.0,
        volume=1000,
    )
    sig = strat.on_candle(candle, sample_data)
    assert sig.side in (SignalSide.BUY, SignalSide.SELL, SignalSide.HOLD)


def test_vwap_strategy(sample_data: pd.DataFrame):
    strat = VWAPStrategy(deviation_pct=1.0)
    signals = strat.generate_signals(sample_data)
    assert isinstance(signals, pd.Series)

    candle = Candle(
        timestamp=datetime.now(),
        open=100.0,
        high=102.0,
        low=99.0,
        close=101.0,
        volume=1000,
    )
    sig = strat.on_candle(candle, sample_data)
    assert sig.side in (SignalSide.BUY, SignalSide.SELL, SignalSide.HOLD)


def test_vwap_strategy_custom_params():
    strat = VWAPStrategy(deviation_pct=2.5)
    assert strat.deviation_pct == 2.5


def test_rsi_pullback_strategy(sample_data: pd.DataFrame):
    strat = RSIPullbackStrategy(period=14, oversold=30.0, overbought=70.0)
    signals = strat.generate_signals(sample_data)
    assert isinstance(signals, pd.Series)

    candle = Candle(
        timestamp=datetime.now(),
        open=100.0,
        high=102.0,
        low=99.0,
        close=101.0,
        volume=1000,
    )
    sig = strat.on_candle(candle, sample_data)
    assert sig.side in (SignalSide.BUY, SignalSide.SELL, SignalSide.HOLD)


def test_orb_strategy(sample_data: pd.DataFrame):
    strat = ORBStrategy(breakout_candles=5)
    signals = strat.generate_signals(sample_data)
    assert isinstance(signals, pd.Series)

    candle = Candle(
        timestamp=datetime.now(),
        open=100.0,
        high=102.0,
        low=99.0,
        close=101.0,
        volume=1000,
    )
    sig = strat.on_candle(candle, sample_data)
    assert sig.side in (SignalSide.BUY, SignalSide.SELL, SignalSide.HOLD)


def test_orb_strategy_custom_params():
    strat = ORBStrategy(breakout_candles=10)
    assert strat.breakout_candles == 10


def test_mean_reversion_strategy(sample_data: pd.DataFrame):
    strat = MeanReversionStrategy(period=15, std_dev=2.0)
    signals = strat.generate_signals(sample_data)
    assert isinstance(signals, pd.Series)

    candle = Candle(
        timestamp=datetime.now(),
        open=100.0,
        high=102.0,
        low=99.0,
        close=101.0,
        volume=1000,
    )
    sig = strat.on_candle(candle, sample_data)
    assert sig.side in (SignalSide.BUY, SignalSide.SELL, SignalSide.HOLD)
