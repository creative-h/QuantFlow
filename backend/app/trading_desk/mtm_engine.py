"""Mark-To-Market (MTM) Engine computing tick-by-tick real-time portfolio PnL."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class PositionMTMSnapshot:
    """Dataclass storing live tick-by-tick MTM telemetry for an open position."""

    trade_id: str
    instrument: str
    quantity: int
    entry_price: float
    current_ltp: float
    unrealized_pnl: float
    pnl_pct: float
    todays_mtm: float
    running_status: str  # "RUNNING_PROFIT", "RUNNING_LOSS"
    high_since_entry: float
    low_since_entry: float


@dataclass
class PortfolioMTMHeader:
    """Dataclass storing aggregate portfolio MTM metrics (Zerodha Kite style)."""

    todays_mtm: float
    total_mtm: float
    running_profit: float
    running_loss: float
    net_portfolio_pnl: float
    open_positions_count: int


class MTMEngine:
    """Mark-To-Market (MTM) Engine calculating real-time mark-to-market PnL."""

    @classmethod
    def calculate_position_mtm(
        cls,
        trade_id: str,
        instrument: str,
        quantity: int,
        entry_price: float,
        current_ltp: float,
        prev_close_price: Optional[float] = None,
    ) -> PositionMTMSnapshot:
        """Calculate tick-by-tick mark-to-market PnL for an open position."""
        pnl = round((current_ltp - entry_price) * quantity, 2)
        pnl_pct = round(((current_ltp - entry_price) / entry_price) * 100.0, 2)

        prev_p = prev_close_price or entry_price
        todays_mtm = round((current_ltp - prev_p) * quantity, 2)
        running_status = "RUNNING_PROFIT" if pnl >= 0 else "RUNNING_LOSS"

        return PositionMTMSnapshot(
            trade_id=trade_id,
            instrument=instrument,
            quantity=quantity,
            entry_price=entry_price,
            current_ltp=current_ltp,
            unrealized_pnl=pnl,
            pnl_pct=pnl_pct,
            todays_mtm=todays_mtm,
            running_status=running_status,
            high_since_entry=max(entry_price, current_ltp),
            low_since_entry=min(entry_price, current_ltp),
        )

    @classmethod
    def get_portfolio_mtm_header(cls, positions: List[PositionMTMSnapshot]) -> PortfolioMTMHeader:
        """Aggregate tick-by-tick portfolio MTM header."""
        total_pnl = sum(p.unrealized_pnl for p in positions)
        todays_mtm = sum(p.todays_mtm for p in positions)
        running_profit = sum(p.unrealized_pnl for p in positions if p.unrealized_pnl > 0)
        running_loss = sum(p.unrealized_pnl for p in positions if p.unrealized_pnl < 0)

        return PortfolioMTMHeader(
            todays_mtm=round(todays_mtm, 2),
            total_mtm=round(total_pnl, 2),
            running_profit=round(running_profit, 2),
            running_loss=round(running_loss, 2),
            net_portfolio_pnl=round(total_pnl, 2),
            open_positions_count=len(positions),
        )
