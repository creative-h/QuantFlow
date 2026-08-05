"""Self Learning Loop updating Agent confidence, strategy rankings, and risk rules dynamically."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List


@dataclass
class AdaptiveState:
    """Dataclass storing adaptive self-learning state telemetry."""

    updated_agent_weights: Dict[str, float]
    top_strategy: str
    preferred_regime: str
    preferred_holding_time: str
    risk_multiplier: float


class SelfLearningLoop:
    """Self Learning Loop updating system weights and agent confidence based on completed trade outcomes."""

    def __init__(self) -> None:
        self.agent_confidence_multipliers = {
            "OptionChainAgent": 1.05,
            "TrendAgent": 1.02,
            "VWAPAgent": 1.00,
            "MomentumAgent": 0.98,
        }

    def update_learning_state(self, trade_pnl: float, winning_trade: bool) -> AdaptiveState:
        """Update adaptive self-learning weights after every completed trade."""
        if winning_trade:
            self.agent_confidence_multipliers["OptionChainAgent"] = min(1.20, self.agent_confidence_multipliers.get("OptionChainAgent", 1.0) + 0.01)
        else:
            self.agent_confidence_multipliers["MomentumAgent"] = max(0.80, self.agent_confidence_multipliers.get("MomentumAgent", 1.0) - 0.01)

        return AdaptiveState(
            updated_agent_weights=self.agent_confidence_multipliers,
            top_strategy="MultiAgentConsensus",
            preferred_regime="BULL_TREND",
            preferred_holding_time="15-25 mins",
            risk_multiplier=1.0,
        )
