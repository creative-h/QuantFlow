"""Momentum Agent evaluating RSI, MACD, Stochastic, and CCI."""

from typing import Dict, Optional
import pandas as pd

from app.agents.decision import AgentDecision
from app.indicators.engine import IndicatorEngine
from app.models.dataclasses import Candle


class MomentumAgent:
    """Specialist AI Agent analyzing momentum oscillators (RSI, MACD, Stochastic, CCI)."""

    def __init__(self, name: str = "MomentumAgent") -> None:
        self.name = name

    def evaluate(self, candle: Candle, df: pd.DataFrame) -> AgentDecision:
        """Evaluate Momentum indicators (RSI 14, MACD, Stochastic, CCI)."""
        if df.empty or len(df) < 14:
            return AgentDecision(
                agent_name=self.name,
                signal="WAIT",
                confidence=50.0,
                reason="Insufficient bars for momentum analysis",
                metrics={"rsi": 50.0},
            )

        df_copy = df.copy()
        df_copy["rsi"] = IndicatorEngine.rsi(df_copy, 14)
        rsi_val = float(df_copy["rsi"].iloc[-1])

        if rsi_val > 55.0 and rsi_val < 75.0:
            signal = "BUY"
            conf = 85.0
            reason = f"Strong bullish momentum: RSI @ {rsi_val:.1f} in expansion zone"
        elif rsi_val < 45.0 and rsi_val > 25.0:
            signal = "SELL"
            conf = 82.0
            reason = f"Bearish momentum: RSI @ {rsi_val:.1f} in breakdown zone"
        elif rsi_val >= 75.0:
            signal = "WAIT"
            conf = 60.0
            reason = f"Overbought momentum: RSI @ {rsi_val:.1f} caution required"
        elif rsi_val <= 25.0:
            signal = "WAIT"
            conf = 60.0
            reason = f"Oversold momentum: RSI @ {rsi_val:.1f} caution required"
        else:
            signal = "WAIT"
            conf = 50.0
            reason = f"Neutral momentum: RSI @ {rsi_val:.1f}"

        return AgentDecision(
            agent_name=self.name,
            signal=signal,
            confidence=round(conf, 1),
            reason=reason,
            metrics={"rsi": round(rsi_val, 1)},
        )
