"""Trade Journal for audit logging, snapshots, and trade summaries."""

from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

import pandas as pd
from loguru import logger

from app.paper.portfolio.trade import Trade


@dataclass
class JournalEntry:
    """Individual trade journal entry."""

    trade_id: str
    order_id: str
    symbol: str
    side: str
    quantity: int
    price: float
    commission: float
    slippage: float
    realized_pnl: float
    timestamp: str
    notes: Optional[str] = None


class TradeJournal:
    """Journal logging trade execution audit records and portfolio equity snapshots."""

    def __init__(self) -> None:
        self.entries: list[JournalEntry] = []
        self.equity_snapshots: list[dict[str, Any]] = []

    def log_trade(self, trade: Trade, notes: Optional[str] = None) -> JournalEntry:
        """Log a trade execution into the journal."""
        entry = JournalEntry(
            trade_id=trade.trade_id,
            order_id=trade.order_id,
            symbol=trade.symbol,
            side=trade.side.value,
            quantity=trade.quantity,
            price=float(trade.price),
            commission=float(trade.commission),
            slippage=float(trade.slippage),
            realized_pnl=float(trade.realized_pnl),
            timestamp=trade.timestamp.isoformat()
            if trade.timestamp
            else datetime.now().isoformat(),
            notes=notes,
        )
        self.entries.append(entry)
        logger.info(
            "Trade logged in journal: {} {} x {} @ {}",
            entry.side,
            entry.quantity,
            entry.symbol,
            entry.price,
        )
        return entry

    def record_snapshot(
        self, timestamp: datetime, equity: Decimal, cash: Decimal, drawdown: Decimal
    ) -> None:
        """Record portfolio equity snapshot."""
        snapshot = {
            "timestamp": timestamp.isoformat()
            if isinstance(timestamp, datetime)
            else timestamp,
            "equity": float(equity),
            "cash": float(cash),
            "drawdown": float(drawdown),
        }
        self.equity_snapshots.append(snapshot)

    def to_dataframe(self) -> pd.DataFrame:
        """Return journal entries as a pandas DataFrame."""
        if not self.entries:
            return pd.DataFrame(
                columns=[
                    "trade_id",
                    "order_id",
                    "symbol",
                    "side",
                    "quantity",
                    "price",
                    "commission",
                    "slippage",
                    "realized_pnl",
                    "timestamp",
                    "notes",
                ]
            )
        return pd.DataFrame([asdict(e) for e in self.entries])
