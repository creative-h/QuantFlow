"""Agent Decision Structure for Multi-Agent AI System."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class AgentDecision:
    """Dataclass storing signal, confidence, reason, and telemetry metrics from an AI agent."""

    agent_name: str
    signal: str  # "BUY", "SELL", "WAIT"
    confidence: float  # 0.0 to 100.0
    reason: str
    metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
