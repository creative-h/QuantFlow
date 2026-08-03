"""Position sizing models."""

import math


class PositionSizer:
    """Calculates order position sizes based on capital, risk percentage, or volatility (ATR)."""

    @staticmethod
    def fixed_quantity(quantity: int = 100) -> int:
        """Fixed quantity per trade."""
        return max(1, quantity)

    @staticmethod
    def fixed_capital(capital_per_trade: float, asset_price: float) -> int:
        """Fixed capital allocation per trade."""
        if asset_price <= 0:
            return 1
        return max(1, int(capital_per_trade / asset_price))

    @staticmethod
    def risk_percentage(
        account_equity: float,
        risk_pct: float,
        entry_price: float,
        stop_loss_price: float,
    ) -> int:
        """Calculate quantity based on fixed account risk % and stop loss distance."""
        risk_amount = account_equity * (risk_pct / 100.0)
        price_risk = abs(entry_price - stop_loss_price)
        if price_risk <= 0:
            return 1
        qty = math.floor(risk_amount / price_risk)
        return max(1, qty)

    @staticmethod
    def atr_volatility(
        account_equity: float,
        risk_pct: float,
        atr_value: float,
        atr_multiplier: float = 2.0,
    ) -> int:
        """Calculate quantity based on ATR volatility risk."""
        risk_amount = account_equity * (risk_pct / 100.0)
        stop_distance = atr_value * atr_multiplier
        if stop_distance <= 0:
            return 1
        qty = math.floor(risk_amount / stop_distance)
        return max(1, qty)
