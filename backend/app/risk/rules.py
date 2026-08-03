"""Risk management rules and boundaries."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass
class TradingRules:
    """Configurable risk rules and constraints."""

    max_position_size: int = 1000
    max_order_size: int = 500
    max_position_value: float = 50000.0
    max_drawdown_pct: float = 20.0
    max_daily_loss: float = 10000.0
    allow_short_selling: bool = True

    def validate_order(
        self,
        symbol: str,
        quantity: int,
        price: Decimal,
        current_position_qty: int,
        current_drawdown_pct: float,
    ) -> tuple[bool, str]:
        """Check order parameters against risk rules."""
        if current_drawdown_pct > self.max_drawdown_pct:
            return (
                False,
                f"Max drawdown limit exceeded ({current_drawdown_pct:.2f}% > {self.max_drawdown_pct}%)",
            )

        if quantity > self.max_order_size:
            return (
                False,
                f"Order quantity {quantity} exceeds max_order_size ({self.max_order_size})",
            )

        new_position_qty = abs(current_position_qty + quantity)
        if new_position_qty > self.max_position_size:
            return (
                False,
                f"Resulting position size {new_position_qty} exceeds max_position_size ({self.max_position_size})",
            )

        order_val = float(price) * quantity
        if order_val > self.max_position_value:
            return (
                False,
                f"Order value {order_val} exceeds max_position_value ({self.max_position_value})",
            )

        return True, "Order approved by risk rules"
