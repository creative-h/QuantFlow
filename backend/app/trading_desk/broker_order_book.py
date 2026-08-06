"""Broker-Style Order Book & Chronological Trade Book Ledger."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class BrokerOrder:
    """Dataclass storing details of an order in the Broker Orderbook."""

    order_id: str
    trade_id: str
    time: datetime
    order_type: str  # "LIMIT", "MARKET", "STOP_LOSS", "BRACKET"
    instrument: str
    side: str  # "BUY", "SELL"
    quantity: int
    executed_qty: int
    average_price: float
    reason: str
    latency_ms: float
    status: str  # "PENDING", "EXECUTED", "REJECTED", "CANCELLED", "COMPLETED"


@dataclass
class TradeBookEvent:
    """Dataclass storing a single execution step event in the Chronological Trade Book."""

    event_id: str
    timestamp: datetime
    trade_id: str
    event_type: str  # "ENTRY_BUY", "PARTIAL_EXIT", "SL_MODIFIED", "TARGET_HIT", "FINAL_EXIT"
    price: float
    quantity: int
    details: str


class BrokerOrderBook:
    """Broker Order Book maintaining orderbook tabs and chronological trade execution ledgers."""

    _instance: Optional["BrokerOrderBook"] = None

    def __init__(self) -> None:
        self.orders: List[BrokerOrder] = []
        self.events: List[TradeBookEvent] = []
        self._seed_sample_orderbook()

    @classmethod
    def get_instance(cls) -> "BrokerOrderBook":
        """Singleton pattern for Broker Order Book."""
        if cls._instance is None:
            cls._instance = BrokerOrderBook()
        return cls._instance

    def add_order(self, order: BrokerOrder) -> None:
        """Add new order to Orderbook."""
        self.orders.append(order)

    def log_trade_event(self, trade_id: str, event_type: str, price: float, quantity: int, details: str) -> TradeBookEvent:
        """Log a new trade execution step to Chronological Trade Book."""
        event_id = f"EVT_{len(self.events)+1:04d}"
        evt = TradeBookEvent(
            event_id=event_id,
            timestamp=datetime.now(),
            trade_id=trade_id,
            event_type=event_type,
            price=price,
            quantity=quantity,
            details=details,
        )
        self.events.append(evt)
        return evt

    def _seed_sample_orderbook(self) -> None:
        """Seed sample orderbook entries and chronological execution events."""
        self.orders.append(
            BrokerOrder(
                order_id="ORD_9001",
                trade_id="TRD_201",
                time=datetime.now(),
                order_type="MARKET",
                instrument="28th Jul 24250 CE",
                side="BUY",
                quantity=260,
                executed_qty=260,
                average_price=218.50,
                reason="Multi-Agent Consensus BUY Signal",
                latency_ms=48.5,
                status="EXECUTED",
            )
        )

        self.log_trade_event("TRD_201", "ENTRY_BUY", 218.50, 260, "Executed BUY 260 units at ₹218.50")
        self.log_trade_event("TRD_201", "TARGET_HIT", 245.00, 130, "Target 1 hit — Partial profit booked for 130 units")
        self.log_trade_event("TRD_201", "SL_MODIFIED", 218.50, 130, "Break-even Engine moved Stop Loss to entry cost ₹218.50")
