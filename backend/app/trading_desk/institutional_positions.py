"""Sensibull & Zerodha Kite-style Institutional Net Positions & Strategy Grouping Tracker."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class NetPositionItem:
    """Dataclass storing details of a net position item in a strategy group."""

    trade_id: str
    time: datetime
    underlying: str
    instrument: str
    expiry: str
    strike: float
    side: str  # "BUY", "SELL"
    quantity: int
    entry_price: float
    current_price: float
    pnl: float
    unbooked_pnl: float
    booked_pnl: float
    current_rr: float
    holding_time_mins: float
    status: str  # "OPEN", "CLOSED", "NEAR_SL", "NEAR_TARGET"
    ai_confidence: float
    strategy_name: str
    current_recommendation: str  # "HOLD", "BOOK_PARTIAL", "MOVE_SL_COST", "EXIT"


@dataclass
class StrategyGroup:
    """Dataclass storing a Sensibull-style strategy group (e.g. 28 July Expiry)."""

    group_id: str
    group_name: str  # e.g. "28th Jul Expiry"
    expiry: str
    total_pnl: float
    unbooked_pnl: float
    booked_pnl: float
    total_decay: float
    positions: List[NetPositionItem]


class InstitutionalPositionTracker:
    """Institutional Position Tracker managing Net Positions & Strategy Groupings."""

    _instance: Optional["InstitutionalPositionTracker"] = None

    def __init__(self) -> None:
        self.strategy_groups: List[StrategyGroup] = []
        self._seed_sensibull_groups()

    @classmethod
    def get_instance(cls) -> "InstitutionalPositionTracker":
        """Singleton pattern for institutional position tracker."""
        if cls._instance is None:
            cls._instance = InstitutionalPositionTracker()
        return cls._instance

    def get_portfolio_totals(self) -> Dict[str, float]:
        """Return aggregate portfolio Sensibull totals."""
        total_pnl = sum(g.total_pnl for g in self.strategy_groups)
        unbooked_pnl = sum(g.unbooked_pnl for g in self.strategy_groups)
        booked_pnl = sum(g.booked_pnl for g in self.strategy_groups)
        total_decay = sum(g.total_decay for g in self.strategy_groups)

        return {
            "total_pnl": round(total_pnl, 2),
            "unbooked_pnl": round(unbooked_pnl, 2),
            "booked_pnl": round(booked_pnl, 2),
            "total_decay": round(total_decay, 2),
        }

    def _seed_sensibull_groups(self) -> None:
        """Seed sample Sensibull-style strategy groups (28 Jul Expiry, 14 Jul Expiry)."""
        pos1 = NetPositionItem(
            trade_id="TRD_201",
            time=datetime.now(),
            underlying="NIFTY",
            instrument="28th Jul 24050 CE",
            expiry="28 Jul",
            strike=24050.0,
            side="BUY",
            quantity=0,
            entry_price=185.0,
            current_price=0.25,
            pnl=6451.0,
            unbooked_pnl=0.0,
            booked_pnl=6451.0,
            current_rr=3.2,
            holding_time_mins=45.0,
            status="CLOSED",
            ai_confidence=91.0,
            strategy_name="EMA_VWAP_Crossover",
            current_recommendation="CLOSED",
        )

        pos2 = NetPositionItem(
            trade_id="TRD_202",
            time=datetime.now(),
            underlying="NIFTY",
            instrument="28th Jul 24250 CE",
            expiry="28 Jul",
            strike=24250.0,
            side="BUY",
            quantity=260,
            entry_price=218.50,
            current_price=0.10,
            pnl=-56784.0,
            unbooked_pnl=-56784.0,
            booked_pnl=0.0,
            current_rr=0.2,
            holding_time_mins=120.0,
            status="NEAR_SL",
            ai_confidence=74.0,
            strategy_name="OptionChainBreakout",
            current_recommendation="MOVE_SL_COST",
        )

        pos3 = NetPositionItem(
            trade_id="TRD_203",
            time=datetime.now(),
            underlying="NIFTY",
            instrument="28th Jul 24550 CE",
            expiry="28 Jul",
            strike=24550.0,
            side="SELL",
            quantity=-260,
            entry_price=90.30,
            current_price=0.10,
            pnl=23452.0,
            unbooked_pnl=23452.0,
            booked_pnl=0.0,
            current_rr=2.8,
            holding_time_mins=120.0,
            status="NEAR_TARGET",
            ai_confidence=88.0,
            strategy_name="ShortStraddle",
            current_recommendation="BOOK_PARTIAL",
        )

        group1 = StrategyGroup(
            group_id="GRP_01",
            group_name="28th Jul Expiry",
            expiry="28 Jul",
            total_pnl=-26881.0,
            unbooked_pnl=-33332.0,
            booked_pnl=6451.0,
            total_decay=0.0,
            positions=[pos1, pos2, pos3],
        )

        self.strategy_groups.append(group1)
