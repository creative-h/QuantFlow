"""Decision Manager combining opinions from 10 specialist AI agents with weighted voting."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd

from app.agents.decision import AgentDecision
from app.agents.momentum_agent import MomentumAgent
from app.agents.oi_agent import OIAgent
from app.agents.option_chain_agent import OptionChainAgent
from app.agents.pcr_agent import PCRAgent
from app.agents.price_action_agent import PriceActionAgent
from app.agents.risk_agent import RiskAgent
from app.agents.trend_agent import TrendAgent
from app.agents.volatility_agent import VolatilityAgent
from app.agents.volume_agent import VolumeAgent
from app.agents.vwap_agent import VWAPAgent
from app.models.dataclasses import Candle


@dataclass
class MultiAgentConsensus:
    """Dataclass storing synthesized consensus decision across all 10 specialist agents."""

    symbol: str
    timestamp: datetime
    final_signal: str  # "BUY", "SELL", "WAIT"
    confidence: float  # 0 to 100
    summary_reason: str
    agent_decisions: List[AgentDecision] = field(default_factory=list)
    voting_distribution: Dict[str, float] = field(default_factory=dict)


class DecisionManager:
    """Production Multi-Agent Decision Manager orchestrating 10 specialist agents with weighted voting."""

    DEFAULT_WEIGHTS = {
        "TrendAgent": 0.30,
        "OptionChainAgent": 0.20,
        "MomentumAgent": 0.15,
        "VWAPAgent": 0.10,
        "PriceActionAgent": 0.10,
        "VolumeAgent": 0.05,
        "PCRAgent": 0.05,
        "VolatilityAgent": 0.03,
        "RiskAgent": 0.02,
    }

    def __init__(self, weights: Optional[Dict[str, float]] = None) -> None:
        self.weights = weights or dict(self.DEFAULT_WEIGHTS)
        self.agents = [
            TrendAgent(),
            OptionChainAgent(),
            MomentumAgent(),
            VWAPAgent(),
            PriceActionAgent(),
            VolumeAgent(),
            PCRAgent(),
            OIAgent(),
            VolatilityAgent(),
            RiskAgent(),
        ]

    def evaluate_consensus(self, candle: Candle, df: pd.DataFrame) -> MultiAgentConsensus:
        """Run all specialist AI agents and compute weighted voting consensus."""
        symbol = getattr(candle, "symbol", "NIFTY") or "NIFTY"
        agent_decisions: List[AgentDecision] = []

        buy_weight = 0.0
        sell_weight = 0.0
        wait_weight = 0.0

        total_conf_weight = 0.0
        weighted_conf_sum = 0.0

        for agent in self.agents:
            try:
                dec = agent.evaluate(candle, df)
                agent_decisions.append(dec)

                w = self.weights.get(dec.agent_name, 0.05)
                weighted_conf_sum += dec.confidence * w
                total_conf_weight += w

                if dec.signal == "BUY":
                    buy_weight += w
                elif dec.signal == "SELL":
                    sell_weight += w
                else:
                    wait_weight += w
            except Exception as e:
                pass

        norm_total = max(0.001, buy_weight + sell_weight + wait_weight)
        buy_pct = round((buy_weight / norm_total) * 100.0, 1)
        sell_pct = round((sell_weight / norm_total) * 100.0, 1)
        wait_pct = round((wait_weight / norm_total) * 100.0, 1)

        voting_dist = {"BUY": buy_pct, "SELL": sell_pct, "WAIT": wait_pct}

        avg_conf = round(weighted_conf_sum / max(0.001, total_conf_weight), 1)

        if buy_weight >= sell_weight and buy_weight >= wait_weight and avg_conf >= 70.0:
            final_sig = "BUY"
            summary = f"Multi-Agent Consensus: BUY {symbol} ({buy_pct}% consensus weight with {avg_conf}% confidence)"
        elif sell_weight > buy_weight and sell_weight >= wait_weight and avg_conf >= 70.0:
            final_sig = "SELL"
            summary = f"Multi-Agent Consensus: SELL {symbol} ({sell_pct}% consensus weight with {avg_conf}% confidence)"
        else:
            final_sig = "WAIT"
            summary = f"Multi-Agent Consensus: WAIT {symbol} (Consolidation regime: BUY {buy_pct}%, WAIT {wait_pct}%)"

        return MultiAgentConsensus(
            symbol=symbol,
            timestamp=datetime.now(),
            final_signal=final_sig,
            confidence=avg_conf,
            summary_reason=summary,
            agent_decisions=agent_decisions,
            voting_distribution=voting_dist,
        )
