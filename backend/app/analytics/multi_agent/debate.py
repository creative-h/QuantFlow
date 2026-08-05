"""AI Analyst Debate Engine providing structured multi-agent discussion."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from app.analytics.multi_agent.decision import AITradeDecision, AgentOpinion


@dataclass
class DebateParticipant:
    """Dataclass holding sub-agent participant details in the AI Debate."""

    name: str
    role: str
    vote: str  # "BUY", "SELL", "WAIT"
    confidence: float
    key_argument: str


@dataclass
class AIDebateSession:
    """Structured AI Debate Session holding sub-agent perspectives and final consensus."""

    timestamp: datetime
    participants: List[DebateParticipant] = field(default_factory=list)
    consensus_action: str = "WAIT"
    consensus_confidence: float = 75.0
    summary_reasoning: str = ""


class AIDebateEngine:
    """Engine orchestrating the AI Analyst Debate meeting."""

    ROLE_MAPPING = {
        "TrendAgent": "Macro Trend & Structure Analyst",
        "MomentumAgent": "Candle & RSI Momentum Analyst",
        "VWAPAgent": "Institutional VWAP & Level Specialist",
        "OptionsOIAnalyzer": "Options Open Interest & PCR Analyst",
        "RiskAgent": "Chief Risk Officer (CRO)",
        "MarketRegimeAgent": "Market Regime Specialist",
        "NewsSentimentAgent": "Sentiment & News Analyst",
    }

    @classmethod
    def create_debate(cls, decision: AITradeDecision) -> AIDebateSession:
        """Construct structured AI Debate Session from sub-agent opinions."""
        participants: List[DebateParticipant] = []

        for op in decision.agent_opinions:
            role = cls.ROLE_MAPPING.get(op.agent_name, "Quantitative Analyst")
            vote = "BUY" if op.recommendation == "BULLISH" else ("SELL" if op.recommendation == "BEARISH" else "WAIT")
            participants.append(
                DebateParticipant(
                    name=op.agent_name,
                    role=role,
                    vote=vote,
                    confidence=op.confidence,
                    key_argument=op.reason,
                )
            )

        summary = (
            f"The AI Analyst Team conducted a trade meeting for {decision.symbol}. "
            f"Consensus reached: {decision.action} {decision.symbol} {int(decision.strike)} {decision.option_type} "
            f"with {decision.confidence}% overall confidence."
        )

        return AIDebateSession(
            timestamp=decision.timestamp,
            participants=participants,
            consensus_action=decision.action,
            consensus_confidence=decision.confidence,
            summary_reasoning=summary,
        )
