"""Unit tests for IndicatorEngine and technical indicators."""

import numpy as np
import pandas as pd
import pytest

from app.indicators.engine import IndicatorEngine


@pytest.fixture
def sample_ohlcv_df() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=30, freq="D")
    np.random.seed(42)
    close = 100.0 + np.cumsum(np.random.randn(30) * 2.0)
    high = close + np.abs(np.random.randn(30) * 1.5)
    low = close - np.abs(np.random.randn(30) * 1.5)
    open_p = low + (high - low) * 0.5
    volume = 1000 + np.random.randint(0, 500, 30)

    return pd.DataFrame(
        {"open": open_p, "high": high, "low": low, "close": close, "volume": volume},
        index=dates,
    )


def test_indicator_engine_ema(sample_ohlcv_df: pd.DataFrame):
    ema = IndicatorEngine.ema(sample_ohlcv_df, period=10)
    assert isinstance(ema, pd.Series)
    assert len(ema) == 30
    assert not ema.iloc[-1] == np.nan


def test_indicator_engine_rsi(sample_ohlcv_df: pd.DataFrame):
    rsi = IndicatorEngine.rsi(sample_ohlcv_df, period=14)
    assert isinstance(rsi, pd.Series)
    valid_rsi = rsi.dropna()
    assert (valid_rsi >= 0).all() and (valid_rsi <= 100).all()


def test_indicator_engine_atr(sample_ohlcv_df: pd.DataFrame):
    atr = IndicatorEngine.atr(sample_ohlcv_df, period=14)
    assert isinstance(atr, pd.Series)
    valid_atr = atr.dropna()
    assert (valid_atr > 0).all()


def test_indicator_engine_macd(sample_ohlcv_df: pd.DataFrame):
    macd_df = IndicatorEngine.macd(sample_ohlcv_df, fast=12, slow=26, signal=9)
    assert isinstance(macd_df, pd.DataFrame)
    assert list(macd_df.columns) == ["macd", "signal", "histogram"]
    assert len(macd_df) == 30


def test_indicator_engine_vwap(sample_ohlcv_df: pd.DataFrame):
    vwap = IndicatorEngine.vwap(sample_ohlcv_df)
    assert isinstance(vwap, pd.Series)
    assert len(vwap) == 30
    assert (vwap > 0).all()


def test_indicator_engine_adx(sample_ohlcv_df: pd.DataFrame):
    adx_df = IndicatorEngine.adx(sample_ohlcv_df, period=14)
    assert isinstance(adx_df, pd.DataFrame)
    assert list(adx_df.columns) == ["adx", "plus_di", "minus_di"]
    assert len(adx_df) == 30


def test_indicator_engine_supertrend(sample_ohlcv_df: pd.DataFrame):
    st_df = IndicatorEngine.supertrend(sample_ohlcv_df, period=10, multiplier=3.0)
    assert isinstance(st_df, pd.DataFrame)
    assert list(st_df.columns) == ["supertrend", "direction"]
    assert len(st_df) == 30
    assert set(st_df["direction"].unique()).issubset({1, -1})


def test_indicator_engine_bollinger_bands(sample_ohlcv_df: pd.DataFrame):
    bb_df = IndicatorEngine.bollinger_bands(sample_ohlcv_df, period=20, std_dev=2.0)
    assert isinstance(bb_df, pd.DataFrame)
    assert list(bb_df.columns) == ["upper", "middle", "lower"]
    assert len(bb_df) == 30

    valid_bb = bb_df.dropna()
    assert (valid_bb["upper"] >= valid_bb["middle"]).all()
    assert (valid_bb["middle"] >= valid_bb["lower"]).all()
