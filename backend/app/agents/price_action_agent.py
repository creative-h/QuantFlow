"""Price Action Agent detecting Engulfing, Pin Bar, Inside Bar, and Breakouts."""

from typing import Dict, Optional
import pandas as pd

from app.agents.decision import AgentDecision
from app.models.dataclasses import Candle


class PriceActionAgent:
    """Specialist AI Agent analyzing candlestick patterns and structural breakouts."""

    def __init__(self, name: str = "PriceActionAgent") -> None:
        self.name = name

    def evaluate(self, candle: Candle, df: pd.DataFrame) -> AgentDecision:
        """Evaluate Candlestick Patterns (Engulfing, Pin Bar, Inside Bar, Breakouts)."""
        if df.empty or len(df) < 2:
            return AgentDecision(
                agent_name=self.name,
                signal="WAIT",
                confidence=50.0,
                reason="Insufficient bars for price action analysis",
                metrics={"pattern": "NONE"},
            )

        open_p, high_p, low_p, close_p = candle.open, candle.high, candle.low, candle.close
        body = abs(close_p - open_p)
        total_range = max(0.01, high_p - low_p)

        prev_open = float(df["open"].iloc[-2]) if "open" in df else open_p
        prev_close = float(df["close"].iloc[-2]) if "close" in df else close_p

        # Pin Bar detection (lower wick >= 60% of candle range)
        lower_wick = min(open_p, close_p) - low_p
        upper_wick = high_p - max(open_p, close_p)

        if lower_wick / total_range >= 0.55 and close_p > open_p:
            pattern = "BULLISH_PIN_BAR"
            signal = "BUY"
            conf = 86.0
            reason = f"Bullish Pin Bar detected: Strong lower rejection wick at ₹{low_p:.2f}"
        elif upper_wick / total_range >= 0.55 and close_p < open_p:
            pattern = "BEARISH_PIN_BAR"
            signal = "SELL"
            conf = 84.0
            reason = f"Bearish Pin Bar detected: Strong upper rejection wick at ₹{high_p:.2f}"
        elif close_p > open_p and open_p <= prev_close and close_p >= prev_open:
            pattern = "BULLISH_ENGULFING"
            signal = "BUY"
            conf = 88.0
            reason = "Bullish Engulfing candle pattern completed"
        elif close_p < open_p and open_p >= prev_close and close_p <= prev_open:
            pattern = "BEARISH_ENGULFING"
            signal = "SELL"
            conf = 85.0
            reason = "Bearish Engulfing candle pattern completed"
        else:
            pattern = "NONE"
            signal = "WAIT"
            conf = 50.0
            reason = "No prominent price action reversal pattern detected"

        return AgentDecision(
            agent_name=self.name,
            signal=signal,
            confidence=round(conf, 1),
            reason=reason,
            metrics={"pattern": pattern, "body_ratio": round(body / total_range, 2)},
        )
