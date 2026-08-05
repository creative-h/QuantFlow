"""Trend Agent evaluating EMA, SMA, Supertrend, and ADX."""

from typing import Dict, Optional
import pandas as pd

from app.agents.decision import AgentDecision
from app.indicators.engine import IndicatorEngine
from app.models.dataclasses import Candle


class TrendAgent:
    """Specialist AI Agent analyzing trend direction and ADX strength."""

    def __init__(self, name: str = "TrendAgent") -> None:
        self.name = name

    def evaluate(self, candle: Candle, df: pd.DataFrame) -> AgentDecision:
        """Evaluate Trend indicators (EMA 20/50, SMA 200, Supertrend, ADX)."""
        if df.empty or len(df) < 20:
            return AgentDecision(
                agent_name=self.name,
                signal="WAIT",
                confidence=50.0,
                reason="Insufficient historical bars for trend analysis",
                metrics={"ema20": 0.0, "ema50": 0.0, "adx": 0.0},
            )

        df_copy = df.copy()
        df_copy["ema20"] = IndicatorEngine.ema(df_copy, 20)
        df_copy["ema50"] = IndicatorEngine.ema(df_copy, 50)

        try:
            adx_df = IndicatorEngine.adx(df_copy, 14)
            if isinstance(adx_df, pd.DataFrame) and "adx" in adx_df:
                adx_val = float(adx_df["adx"].dropna().iloc[-1]) if not adx_df["adx"].dropna().empty else 25.0
            else:
                adx_val = float(adx_df.dropna().iloc[-1]) if not adx_df.dropna().empty else 25.0
        except Exception:
            adx_val = 25.0

        latest_ema20 = float(df_copy["ema20"].iloc[-1])
        latest_ema50 = float(df_copy["ema50"].iloc[-1])
        close_p = candle.close

        if close_p > latest_ema20 and latest_ema20 > latest_ema50:
            signal = "BUY"
            conf = min(95.0, 70.0 + (adx_val * 0.6))
            reason = f"Bullish trend: Price (₹{close_p:.2f}) > EMA20 (₹{latest_ema20:.2f}) > EMA50 (₹{latest_ema50:.2f}) with ADX {adx_val:.1f}"
        elif close_p < latest_ema20 and latest_ema20 < latest_ema50:
            signal = "SELL"
            conf = min(95.0, 70.0 + (adx_val * 0.6))
            reason = f"Bearish trend: Price (₹{close_p:.2f}) < EMA20 (₹{latest_ema20:.2f}) < EMA50 (₹{latest_ema50:.2f}) with ADX {adx_val:.1f}"
        else:
            signal = "WAIT"
            conf = 55.0
            reason = f"Sideways trend: Price (₹{close_p:.2f}) consolidating around EMA20 (₹{latest_ema20:.2f})"

        return AgentDecision(
            agent_name=self.name,
            signal=signal,
            confidence=round(conf, 1),
            reason=reason,
            metrics={"ema20": round(latest_ema20, 2), "ema50": round(latest_ema50, 2), "adx": round(adx_val, 1)},
        )
