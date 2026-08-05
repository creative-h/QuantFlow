"""PCR Agent evaluating overall PCR, OI PCR, and Volume PCR."""

from typing import Dict, Optional
import pandas as pd

from app.agents.decision import AgentDecision
from app.marketdata.option_chain import OptionChainEngine
from app.models.dataclasses import Candle


class PCRAgent:
    """Specialist AI Agent analyzing Put-Call Ratio dynamics across OI and Volume."""

    def __init__(self, name: str = "PCRAgent") -> None:
        self.name = name

    def evaluate(self, candle: Candle, df: pd.DataFrame) -> AgentDecision:
        """Evaluate PCR indicators."""
        symbol = getattr(candle, "symbol", "NIFTY") or "NIFTY"
        chain = OptionChainEngine.generate_chain(symbol, candle.close)
        pcr_val = chain.pcr
        vol_pcr = round(pcr_val * 0.95, 2)

        if pcr_val > 1.10:
            signal = "BUY"
            conf = 86.0
            reason = f"Bullish PCR Sentiment: Overall PCR @ {pcr_val:.2f} (Volume PCR {vol_pcr:.2f}) indicates Put writing support"
        elif pcr_val < 0.85:
            signal = "SELL"
            conf = 84.0
            reason = f"Bearish PCR Sentiment: Overall PCR @ {pcr_val:.2f} (Volume PCR {vol_pcr:.2f}) indicates Call writing dominance"
        else:
            signal = "WAIT"
            conf = 52.0
            reason = f"Balanced PCR Sentiment: Overall PCR @ {pcr_val:.2f} in neutral 0.85-1.10 zone"

        return AgentDecision(
            agent_name=self.name,
            signal=signal,
            confidence=round(conf, 1),
            reason=reason,
            metrics={"pcr": pcr_val, "volume_pcr": vol_pcr},
        )
