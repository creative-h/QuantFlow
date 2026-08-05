"""VWAP Agent evaluating distance from VWAP, VWAP bounce, and rejection."""

from typing import Dict, Optional
import pandas as pd

from app.agents.decision import AgentDecision
from app.indicators.engine import IndicatorEngine
from app.models.dataclasses import Candle


class VWAPAgent:
    """Specialist AI Agent analyzing institutional VWAP levels and bounces."""

    def __init__(self, name: str = "VWAPAgent") -> None:
        self.name = name

    def evaluate(self, candle: Candle, df: pd.DataFrame) -> AgentDecision:
        """Evaluate VWAP levels and distance."""
        if df.empty or len(df) < 5:
            return AgentDecision(
                agent_name=self.name,
                signal="WAIT",
                confidence=50.0,
                reason="Insufficient bars for VWAP analysis",
                metrics={"vwap": 0.0, "distance_pct": 0.0},
            )

        df_copy = df.copy()
        df_copy["vwap"] = IndicatorEngine.vwap(df_copy)
        vwap_val = float(df_copy["vwap"].iloc[-1])
        close_p = candle.close

        dist_pct = round(((close_p - vwap_val) / vwap_val) * 100.0, 2)

        if close_p > vwap_val and dist_pct >= 0.10:
            signal = "BUY"
            conf = 88.0
            reason = f"Bullish VWAP alignment: Price (₹{close_p:.2f}) trading +{dist_pct}% above VWAP (₹{vwap_val:.2f})"
        elif close_p < vwap_val and dist_pct <= -0.10:
            signal = "SELL"
            conf = 85.0
            reason = f"Bearish VWAP alignment: Price (₹{close_p:.2f}) trading {dist_pct}% below VWAP (₹{vwap_val:.2f})"
        else:
            signal = "WAIT"
            conf = 55.0
            reason = f"Price (₹{close_p:.2f}) hugging VWAP line (₹{vwap_val:.2f})"

        return AgentDecision(
            agent_name=self.name,
            signal=signal,
            confidence=round(conf, 1),
            reason=reason,
            metrics={"vwap": round(vwap_val, 2), "distance_pct": dist_pct},
        )
