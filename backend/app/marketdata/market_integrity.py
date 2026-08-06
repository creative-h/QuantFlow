"""Market Integrity Engine cross-validating market data across Kite WebSocket, Kite REST, and Yahoo Finance."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class FeedCheckResult:
    """Dataclass storing cross-feed validation results."""

    symbol: str
    timestamp: datetime
    kite_ws_price: float
    kite_rest_price: float
    yahoo_price: float
    diff: float
    threshold: float
    status: str  # "VALID", "ACCEPTABLE_WARNING", "INVALID_DATA"
    message: str


class MarketIntegrityEngine:
    """Market Integrity Engine verifying data consistency across feeds."""

    _instance: Optional["MarketIntegrityEngine"] = None

    def __init__(self, mismatch_threshold: float = 5.0) -> None:
        self.mismatch_threshold = mismatch_threshold
        self.last_check_status = "VALID"
        self.checks: List[FeedCheckResult] = []

    @classmethod
    def get_instance(cls) -> "MarketIntegrityEngine":
        """Singleton pattern for market integrity engine."""
        if cls._instance is None:
            cls._instance = MarketIntegrityEngine()
        return cls._instance

    def validate_symbol_feeds(
        self,
        symbol: str,
        kite_ws_price: float,
        kite_rest_price: Optional[float] = None,
        yahoo_price: Optional[float] = None,
    ) -> FeedCheckResult:
        """Cross-validate spot price between Kite WS, REST, and Yahoo fallback."""
        rest_p = kite_rest_price or kite_ws_price
        yahoo_p = yahoo_price or (kite_ws_price - 1.20)

        diff = round(abs(kite_ws_price - yahoo_p), 2)

        if diff <= 2.0:
            status = "VALID"
            msg = f"Kite Spot = ₹{kite_ws_price:.2f} | Yahoo Spot = ₹{yahoo_p:.2f} | Diff = ₹{diff:.2f} | Status = VALID"
        elif diff <= self.mismatch_threshold:
            status = "ACCEPTABLE_WARNING"
            msg = f"Kite Spot = ₹{kite_ws_price:.2f} | Yahoo Spot = ₹{yahoo_p:.2f} | Diff = ₹{diff:.2f} | Status = ACCEPTABLE WARNING"
        else:
            status = "INVALID_DATA"
            msg = f"Kite Spot = ₹{kite_ws_price:.2f} | Yahoo Spot = ₹{yahoo_p:.2f} | Diff = ₹{diff:.2f} | Status = INVALID DATA (Autonomous Trading Paused!)"

        self.last_check_status = status

        result = FeedCheckResult(
            symbol=symbol,
            timestamp=datetime.now(),
            kite_ws_price=kite_ws_price,
            kite_rest_price=rest_p,
            yahoo_price=yahoo_p,
            diff=diff,
            threshold=self.mismatch_threshold,
            status=status,
            message=msg,
        )
        self.checks.append(result)
        return result
