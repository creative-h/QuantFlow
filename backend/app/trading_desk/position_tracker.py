"""Live Position Tracker managing open and closed paper trading positions."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class OpenPosition:
    """Dataclass storing details of an active open trade position."""

    trade_id: str
    time: datetime
    underlying: str
    option: str
    side: str  # "BUY", "SELL"
    quantity: int
    entry_price: float
    current_price: float
    pnl: float
    pnl_pct: float
    stop_loss: float
    target1: float
    target2: float
    target3: float
    current_rr: float
    holding_time_mins: float
    status: str = "OPEN"


@dataclass
class ClosedPosition:
    """Dataclass storing details of a closed trade position."""

    trade_id: str
    entry_price: float
    exit_price: float
    exit_reason: str  # "TARGET_1_HIT", "STOP_LOSS_HIT", "TRAILING_STOP", "TIME_EXIT", "MANUAL"
    pnl: float
    pnl_pct: float
    duration_mins: float
    ai_confidence: float
    timestamp: datetime = field(default_factory=datetime.now)


class PositionTracker:
    """Position Tracker maintaining real-time open and closed position tables."""

    _instance: Optional["PositionTracker"] = None

    def __init__(self) -> None:
        self.open_positions: List[OpenPosition] = []
        self.closed_positions: List[ClosedPosition] = []
        self._seed_sample_positions()

    @classmethod
    def get_instance(cls) -> "PositionTracker":
        """Singleton pattern for position tracker."""
        if cls._instance is None:
            cls._instance = PositionTracker()
        return cls._instance

    def add_open_position(self, pos: OpenPosition) -> None:
        """Add a new open position."""
        self.open_positions.append(pos)

    def close_position(self, trade_id: str, exit_price: float, exit_reason: str) -> Optional[ClosedPosition]:
        """Close an open position and add to closed positions table."""
        pos = next((p for p in self.open_positions if p.trade_id == trade_id), None)
        if not pos:
            return None

        self.open_positions.remove(pos)

        pnl = (exit_price - pos.entry_price) * pos.quantity
        pnl_pct = ((exit_price - pos.entry_price) / pos.entry_price) * 100.0

        closed_pos = ClosedPosition(
            trade_id=pos.trade_id,
            entry_price=pos.entry_price,
            exit_price=exit_price,
            exit_reason=exit_reason,
            pnl=round(pnl, 2),
            pnl_pct=round(pnl_pct, 2),
            duration_mins=pos.holding_time_mins,
            ai_confidence=88.5,
        )
        self.closed_positions.append(closed_pos)
        return closed_pos

    def _seed_sample_positions(self) -> None:
        """Seed sample active open and closed trade positions."""
        self.open_positions.append(
            OpenPosition(
                trade_id="TRD_101",
                time=datetime.now(),
                underlying="NIFTY",
                option="NIFTY 24900 CE",
                side="BUY",
                quantity=50,
                entry_price=118.0,
                current_price=132.5,
                pnl=725.0,
                pnl_pct=12.29,
                stop_loss=118.0,  # Moved to cost
                target1=135.0,
                target2=155.0,
                target3=180.0,
                current_rr=2.7,
                holding_time_mins=18.5,
                status="OPEN",
            )
        )

        self.closed_positions.append(
            ClosedPosition(
                trade_id="TRD_100",
                entry_price=105.0,
                exit_price=135.0,
                exit_reason="TARGET_1_HIT",
                pnl=1500.0,
                pnl_pct=28.57,
                duration_mins=24.0,
                ai_confidence=91.0,
            )
        )
