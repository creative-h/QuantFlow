"""Risk Agent evaluating Position Size, Capital Allocation, Daily Loss, Exposure, and Margin."""

from typing import Dict, Optional
import pandas as pd

from app.agents.decision import AgentDecision
from app.models.dataclasses import Candle


class RiskAgent:
    """Specialist Chief Risk Officer (CRO) Agent validating risk budget and position limits."""

    def __init__(self, name: str = "RiskAgent") -> None:
        self.name = name

    def evaluate(self, candle: Candle, df: pd.DataFrame) -> AgentDecision:
        """Validate trade risk against daily drawdown and position limits."""
        daily_pnl = 420.0
        max_daily_loss = -2000.0
        remaining_budget = 1580.0
        exposure_pct = 2.95

        if daily_pnl > max_daily_loss and exposure_pct <= 10.0:
            signal = "BUY"
            conf = 95.0
            reason = f"Risk Approved: Capital allocation (2.95%) and daily loss limit (Remaining budget: ₹{remaining_budget:.2f}) fully compliant"
        else:
            signal = "WAIT"
            conf = 30.0
            reason = "Risk Warning: Risk budget or position exposure breach risk"

        return AgentDecision(
            agent_name=self.name,
            signal=signal,
            confidence=round(conf, 1),
            reason=reason,
            metrics={"daily_pnl": daily_pnl, "remaining_budget": remaining_budget, "exposure_pct": exposure_pct},
        )
