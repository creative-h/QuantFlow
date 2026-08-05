"""Option Chain Agent evaluating Max Pain, Highest OI, and Call/Put writing."""

from typing import Dict, Optional
import pandas as pd

from app.agents.decision import AgentDecision
from app.marketdata.option_chain import OptionChain, OptionChainEngine
from app.models.dataclasses import Candle


class OptionChainAgent:
    """Specialist AI Agent analyzing live Option Chain matrix, Max Pain, and Call/Put writing dynamics."""

    def __init__(self, name: str = "OptionChainAgent") -> None:
        self.name = name

    def evaluate(self, candle: Candle, df: pd.DataFrame) -> AgentDecision:
        """Evaluate Option Chain matrix for symbol."""
        symbol = getattr(candle, "symbol", "NIFTY") or "NIFTY"
        spot = candle.close

        chain: OptionChain = OptionChainEngine.generate_chain(symbol, spot)

        atm = chain.atm_strike
        max_pain = chain.max_pain
        pcr = chain.pcr

        if spot >= chain.support_level and pcr >= 1.05:
            signal = "BUY"
            conf = 88.0
            reason = f"Bullish Option Chain: PCR {pcr:.2f} with strong Put writing support at ₹{chain.support_level:.0f}"
        elif spot <= chain.resistance_level and pcr <= 0.85:
            signal = "SELL"
            conf = 85.0
            reason = f"Bearish Option Chain: PCR {pcr:.2f} with heavy Call writing resistance at ₹{chain.resistance_level:.0f}"
        else:
            signal = "WAIT"
            conf = 55.0
            reason = f"Neutral Option Chain: PCR {pcr:.2f} around Max Pain ₹{max_pain:.0f}"

        return AgentDecision(
            agent_name=self.name,
            signal=signal,
            confidence=round(conf, 1),
            reason=reason,
            metrics={"pcr": pcr, "max_pain": max_pain, "support": chain.support_level, "resistance": chain.resistance_level},
        )
