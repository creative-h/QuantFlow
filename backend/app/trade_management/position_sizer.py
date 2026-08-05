"""Professional Position Sizer supporting Risk-based sizing and Kelly Criterion."""

import math
from typing import Dict, Optional


class ProfessionalPositionSizer:
    """Position Sizer implementing Risk-Based Allocation and Kelly Criterion formulas."""

    @classmethod
    def calculate_risk_based_size(
        cls,
        portfolio_value: float,
        risk_pct: float,
        entry_price: float,
        stop_loss: float,
        lot_size: int = 25,
    ) -> Dict[str, float]:
        """Calculate position size based on fixed risk percentage of portfolio."""
        if entry_price <= 0 or stop_loss >= entry_price or portfolio_value <= 0:
            return {"quantity": lot_size, "lots": 1, "risk_amount": 0.0, "position_value": 0.0}

        risk_amount = portfolio_value * (risk_pct / 100.0)
        risk_per_unit = entry_price - stop_loss
        raw_quantity = risk_amount / risk_per_unit

        lots = max(1, math.floor(raw_quantity / lot_size))
        final_quantity = lots * lot_size
        position_value = final_quantity * entry_price

        return {
            "quantity": final_quantity,
            "lots": lots,
            "risk_amount": round(risk_amount, 2),
            "position_value": round(position_value, 2),
            "actual_risk": round(final_quantity * risk_per_unit, 2),
        }

    @classmethod
    def calculate_kelly_fraction(
        cls,
        win_rate: float,
        reward_risk_ratio: float,
        fractional_kelly: float = 0.5,
    ) -> float:
        """Calculate optimal Kelly Criterion allocation fraction (K = W - (1-W)/R)."""
        if reward_risk_ratio <= 0:
            return 0.01

        w = win_rate / 100.0 if win_rate > 1.0 else win_rate
        r = reward_risk_ratio

        full_kelly = w - ((1.0 - w) / r)
        kelly_fraction = max(0.01, min(0.25, full_kelly * fractional_kelly))
        return round(kelly_fraction, 4)
