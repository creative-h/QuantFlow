"""Rejected Trade Logger storing every rejected trade signal and reason."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class RejectedTrade:
    """Dataclass storing telemetry for a rejected trade signal."""

    rejection_id: str
    timestamp: datetime
    instrument: str
    signal: str  # "BUY", "SELL"
    reason: str
    rejected_by: str  # e.g. "RiskAgent", "PCRAgent", "VolatilityAgent", "DrawdownLimit"


class RejectedTradeLogger:
    """Rejected Trade Logger recording all rejected trades for quantitative auditability."""

    _instance: Optional["RejectedTradeLogger"] = None

    def __init__(self) -> None:
        self.rejected_trades: List[RejectedTrade] = []
        self._seed_sample_rejections()

    @classmethod
    def get_instance(cls) -> "RejectedTradeLogger":
        """Singleton pattern for central rejected trade logger."""
        if cls._instance is None:
            cls._instance = RejectedTradeLogger()
        return cls._instance

    def log_rejection(
        self,
        instrument: str,
        signal: str,
        reason: str,
        rejected_by: str,
    ) -> RejectedTrade:
        """Log a new rejected trade entry."""
        rejection_id = f"REJ_{len(self.rejected_trades)+1:04d}"
        rej = RejectedTrade(
            rejection_id=rejection_id,
            timestamp=datetime.now(),
            instrument=instrument,
            signal=signal,
            reason=reason,
            rejected_by=rejected_by,
        )
        self.rejected_trades.append(rej)
        return rej

    def get_all_rejections(self) -> List[RejectedTrade]:
        """Return all logged trade rejections."""
        return list(reversed(self.rejected_trades))

    def _seed_sample_rejections(self) -> None:
        """Seed sample trade rejections."""
        self.log_rejection(
            instrument="BANKNIFTY 55200 PE",
            signal="SELL",
            reason="PCR below 0.85 threshold (Call writing dominance)",
            rejected_by="PCRAgent",
        )
        self.log_rejection(
            instrument="FINNIFTY 22500 CE",
            signal="BUY",
            reason="Daily drawdown limit (-₹2,000) risk boundary breach",
            rejected_by="RiskAgent",
        )
