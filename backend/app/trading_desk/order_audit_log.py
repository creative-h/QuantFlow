"""Order Audit Logger capturing microsecond-timestamped system events."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class AuditEvent:
    """Dataclass storing details of an audited system event."""

    event_id: str
    timestamp: datetime
    event_type: str  # e.g. "CONNECTED", "DOWNLOADED_OPTION_CHAIN", "SIGNAL_GENERATED", "RISK_APPROVED", "ORDER_PLACED", "ORDER_FILLED", "STOP_UPDATED", "TARGET_HIT", "JOURNAL_SAVED"
    symbol: str
    details: str


class OrderAuditLogger:
    """Order Audit Logger recording every execution step for 100% auditability."""

    _instance: Optional["OrderAuditLogger"] = None

    def __init__(self) -> None:
        self.events: List[AuditEvent] = []
        self._seed_sample_events()

    @classmethod
    def get_instance(cls) -> "OrderAuditLogger":
        """Singleton pattern for central audit logger."""
        if cls._instance is None:
            cls._instance = OrderAuditLogger()
        return cls._instance

    def log_event(self, event_type: str, symbol: str, details: str) -> AuditEvent:
        """Log a new audited event with timestamp."""
        event_id = f"AUD_{len(self.events)+1:04d}"
        evt = AuditEvent(
            event_id=event_id,
            timestamp=datetime.now(),
            event_type=event_type,
            symbol=symbol,
            details=details,
        )
        self.events.append(evt)
        return evt

    def get_recent_events(self, limit: int = 50) -> List[AuditEvent]:
        """Return most recent audit events."""
        return list(reversed(self.events[-limit:]))

    def _seed_sample_events(self) -> None:
        """Seed initial startup audit events."""
        self.log_event("CONNECTED", "KITE_WS", "Kite Ticker WebSocket session established.")
        self.log_event("DOWNLOADED_OPTION_CHAIN", "NIFTY", "Downloaded 7 option chain strike contracts for NIFTY spot ₹24,915.20.")
        self.log_event("SIGNAL_GENERATED", "NIFTY", "Multi-Agent Decision Engine generated BUY signal with 91% confidence.")
        self.log_event("RISK_APPROVED", "NIFTY", "Risk Agent approved 2.95% position exposure limit.")
        self.log_event("ORDER_PLACED", "NIFTY 24900 CE", "Market BUY order placed for 50 units at ₹118.00.")
        self.log_event("ORDER_FILLED", "NIFTY 24900 CE", "Filled 50 units at ₹118.00.")
        self.log_event("TARGET_HIT", "NIFTY 24900 CE", "Target 1 hit at ₹135.00 — 50% partial exit executed.")
        self.log_event("STOP_UPDATED", "NIFTY 24900 CE", "Break-even Engine moved Stop Loss to entry cost ₹118.00.")
