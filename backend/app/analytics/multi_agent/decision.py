"""AI Decision Structure and Agent Opinion Dataclasses."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class AgentOpinion:
    """Dataclass storing score and opinion from an individual AI sub-agent."""

    agent_name: str
    score: float  # 0 to 100
    confidence: float  # 0 to 100
    reason: str
    recommendation: str  # "BULLISH", "BEARISH", "NEUTRAL"


@dataclass
class AITradeDecision:
    """Unified AI Trade Decision Object synthesized by DecisionCoordinator."""

    symbol: str  # e.g. "NIFTY"
    expiry: str  # e.g. "Thursday Weekly"
    strike: float  # e.g. 24900.0
    option_type: str  # "CE" or "PE"
    action: str  # "BUY", "SELL", "WAIT"
    entry: float  # e.g. 118.0
    stop_loss: float  # e.g. 105.0
    target1: float  # e.g. 135.0
    target2: float  # e.g. 150.0
    target3: float  # e.g. 175.0
    confidence: float  # 0 to 100
    expected_hold_time: str  # e.g. "15-30 mins"
    risk_reward: str  # e.g. "1:2.7"
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    market_regime: str = "TRENDING_BULLISH"
    timestamp: datetime = field(default_factory=datetime.now)
    agent_opinions: List[AgentOpinion] = field(default_factory=list)
