"""Unified IndicatorEngine for technical analysis."""

from typing import Any

import pandas as pd

from app.indicators.adx import adx
from app.indicators.atr import atr
from app.indicators.bollinger import bollinger_bands
from app.indicators.ema import ema
from app.indicators.macd import macd
from app.indicators.rsi import rsi
from app.indicators.supertrend import supertrend
from app.indicators.vwap import vwap


class IndicatorEngine:
    """Reusable engine computing standard technical indicators on OHLCV DataFrames or Series."""

    @staticmethod
    def ema(data: pd.DataFrame | pd.Series, period: int = 14) -> pd.Series:
        """Calculate Exponential Moving Average."""
        series = data["close"] if isinstance(data, pd.DataFrame) else data
        return ema(series, period)

    @staticmethod
    def rsi(data: pd.DataFrame | pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index (0–100)."""
        series = data["close"] if isinstance(data, pd.DataFrame) else data
        return rsi(series, period)

    @staticmethod
    def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range."""
        return atr(df["high"], df["low"], df["close"], period)

    @staticmethod
    def macd(
        data: pd.DataFrame | pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> pd.DataFrame:
        """Calculate MACD line, signal line, and histogram."""
        series = data["close"] if isinstance(data, pd.DataFrame) else data
        return macd(series, fast, slow, signal)

    @staticmethod
    def vwap(df: pd.DataFrame) -> pd.Series:
        """Calculate Volume-Weighted Average Price."""
        return vwap(df["high"], df["low"], df["close"], df["volume"])

    @staticmethod
    def adx(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Calculate Average Directional Index (+DI, -DI, ADX)."""
        return adx(df["high"], df["low"], df["close"], period)

    @staticmethod
    def supertrend(
        df: pd.DataFrame, period: int = 10, multiplier: float = 3.0
    ) -> pd.DataFrame:
        """Calculate Supertrend indicator (supertrend line and direction)."""
        return supertrend(df["high"], df["low"], df["close"], period, multiplier)

    @staticmethod
    def bollinger_bands(
        data: pd.DataFrame | pd.Series, period: int = 20, std_dev: float = 2.0
    ) -> pd.DataFrame:
        """Calculate Upper, Middle, Lower Bollinger Bands."""
        series = data["close"] if isinstance(data, pd.DataFrame) else data
        return bollinger_bands(series, period, std_dev)

    @classmethod
    def compute(cls, df: pd.DataFrame, indicator_type: str, **kwargs: Any) -> pd.DataFrame:
        """Compute specified indicator and append columns to DataFrame copy."""
        res_df = df.copy()
        ind_type = indicator_type.lower().strip()
        if ind_type == "supertrend":
            st_df = cls.supertrend(df, **kwargs)
            res_df["supertrend"] = st_df["supertrend"]
            res_df["supertrend_dir"] = st_df["direction"]
        elif ind_type == "vwap":
            res_df["vwap"] = cls.vwap(df)
        elif ind_type == "rsi":
            res_df["rsi"] = cls.rsi(df, **kwargs)
        elif ind_type in ("bollinger", "bollinger_bands"):
            bb = cls.bollinger_bands(df, **kwargs)
            res_df["bb_upper"] = bb["upper"]
            res_df["bb_middle"] = bb["middle"]
            res_df["bb_lower"] = bb["lower"]
        elif ind_type == "ema":
            res_df["ema"] = cls.ema(df, **kwargs)
        elif ind_type == "atr":
            res_df["atr"] = cls.atr(df, **kwargs)
        elif ind_type == "macd":
            m_df = cls.macd(df, **kwargs)
            res_df["macd"] = m_df["macd"]
            res_df["macd_signal"] = m_df["macd_signal"]
            res_df["macd_hist"] = m_df["macd_hist"]
        elif ind_type == "adx":
            adx_df = cls.adx(df, **kwargs)
            res_df["adx"] = adx_df["adx"]
            res_df["plus_di"] = adx_df["plus_di"]
            res_df["minus_di"] = adx_df["minus_di"]
        return res_df
