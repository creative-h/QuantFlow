"""Live Trade Book & Order Lifecycle Manager for institutional trade tracking."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class TradeBookEntry:
    """Dataclass storing details of a trade in the Trade Book."""

    trade_id: str
    timestamp: datetime
    symbol: str
    instrument: str
    direction: str  # "BUY", "SELL"
    entry_price: float
    current_price: float
    stop_loss: float
    target1: float
    target2: float
    quantity: int
    broker_status: str  # "FILLED", "PENDING", "CANCELLED"
    trade_status: str  # "SCANNED", "APPROVED", "EXECUTED", "ACTIVE", "TARGET_HIT", "STOP_HIT", "MANUAL_EXIT"
    pnl: float
    holding_time_mins: float
    ai_confidence: float
    approval_score: float
    reason: str


class LiveTradeBook:
    """Live Trade Book managing trade records and lifecycle state transitions."""

    _instance: Optional["LiveTradeBook"] = None

    def __init__(self) -> None:
        self.trades: List[TradeBookEntry] = []
        self._seed_sample_trade_book()

    @classmethod
    def get_instance(cls) -> "LiveTradeBook":
        """Singleton pattern for Live Trade Book."""
        if cls._instance is None:
            cls._instance = LiveTradeBook()
        return cls._instance

    def add_trade(self, entry: TradeBookEntry) -> None:
        """Add new trade entry to Trade Book."""
        self.trades.append(entry)

    def update_lifecycle(self, trade_id: str, new_status: str) -> Optional[TradeBookEntry]:
        """Update lifecycle state of a trade."""
        trade = next((t for t in self.trades if t.trade_id == trade_id), None)
        if trade:
            trade.trade_status = new_status
        return trade

    def _seed_sample_trade_book(self) -> None:
        """Seed sample institutional trade book entries."""
        self.trades.append(
            TradeBookEntry(
                trade_id="TB_001",
                timestamp=datetime.now(),
                symbol="NIFTY",
                instrument="NIFTY 24900 CE",
                direction="BUY",
                entry_price=118.0,
                current_price=132.5,
                stop_loss=118.0,
                target1=135.0,
                target2=155.0,
                quantity=50,
                broker_status="FILLED",
                trade_status="ACTIVE",
                pnl=725.0,
                holding_time_mins=18.5,
                ai_confidence=91.0,
                approval_score=95.0,
                reason="EMA20 crossover above EMA50 with strong VWAP bounce",
            )
        )
