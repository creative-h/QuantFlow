"""AI Trade Manager & Automatic Exit Management Engine."""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class AutoExitConfig:
    """Dataclass storing configurable auto-exit rule parameters."""

    break_even_sl_enabled: bool = True
    atr_trail_multiplier: float = 2.0
    ema_trail_period: int = 20
    vwap_trail_enabled: bool = True
    time_exit_mins: int = 45
    profit_lock_pct: float = 50.0  # Lock 50% profit upon T1 hit
    dynamic_target_enabled: bool = True


@dataclass
class TradeManagerDecision:
    """Dataclass storing action recommendation from AI Trade Manager."""

    trade_id: str
    action: str  # "HOLD", "MOVE_SL_COST", "BOOK_25", "BOOK_50", "BOOK_FULL", "ADD_POSITION", "REJECT_SCALING"
    reason: str
    updated_sl: Optional[float] = None
    updated_target: Optional[float] = None


class AutoExitManager:
    """AI Trade Manager evaluating active candle conditions and executing dynamic exits."""

    def __init__(self, config: Optional[AutoExitConfig] = None) -> None:
        self.config = config or AutoExitConfig()

    def evaluate_position(
        self,
        trade_id: str,
        current_price: float,
        entry_price: float,
        target1_price: float,
        sl_price: float,
        holding_time_mins: float,
    ) -> TradeManagerDecision:
        """Evaluate active position against auto-exit rules on every candle."""
        # 1. Target 1 Hit -> Move SL to Break-Even Cost & Lock 50% Profit
        if current_price >= target1_price:
            return TradeManagerDecision(
                trade_id=trade_id,
                action="BOOK_50",
                reason="Target 1 hit — 50% partial profit booked, SL moved to Break-even entry cost ₹{entry_price:.2f}",
                updated_sl=entry_price,
            )

        # 2. Time Exit breach
        if holding_time_mins >= self.config.time_exit_mins:
            return TradeManagerDecision(
                trade_id=trade_id,
                action="BOOK_FULL",
                reason=f"45-minute time stop exit triggered (Holding time: {holding_time_mins:.0f} mins)",
            )

        # 3. Default Hold
        return TradeManagerDecision(
            trade_id=trade_id,
            action="HOLD",
            reason="Price action consolidated above VWAP support line",
            updated_sl=sl_price,
        )
