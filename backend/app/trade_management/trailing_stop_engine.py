"""Trailing Stop Engine managing Auto Trail, ATR Stop Loss, Volatility Stop, and Time Stop."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional


class TrailingStopEngine:
    """Trailing Stop Engine dynamically updating trailing stop loss and enforcing time stops."""

    def __init__(
        self,
        entry_price: float,
        initial_stop_loss: float,
        entry_time: Optional[datetime] = None,
        max_holding_time_mins: int = 45,
        atr_multiplier: float = 2.0,
    ) -> None:
        self.entry_price = entry_price
        self.current_stop_loss = initial_stop_loss
        self.highest_price = entry_price
        self.entry_time = entry_time or datetime.now()
        self.max_holding_time_mins = max_holding_time_mins
        self.atr_multiplier = atr_multiplier

    def update_trailing_stop(self, current_price: float, atr: float = 5.0) -> float:
        """Update trailing stop loss based on highest price reached and ATR trailing gap."""
        if current_price > self.highest_price:
            self.highest_price = current_price
            atr_stop = self.highest_price - (atr * self.atr_multiplier)
            self.current_stop_loss = max(self.current_stop_loss, atr_stop)

        return round(self.current_stop_loss, 2)

    def is_time_stop_breached(self, current_time: Optional[datetime] = None) -> bool:
        """Return True if trade holding duration exceeds max allowed time limit."""
        now = current_time or datetime.now()
        elapsed_mins = (now - self.entry_time).total_seconds() / 60.0
        return elapsed_mins >= self.max_holding_time_mins

    def is_stop_loss_breached(self, current_price: float) -> bool:
        """Return True if current price drops at or below current trailing stop loss."""
        return current_price <= self.current_stop_loss
