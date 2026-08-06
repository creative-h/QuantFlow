"""Real Margin Engine calculating SPAN, Exposure, Premium, and Portfolio Margins (Zerodha style)."""

from dataclasses import dataclass
from typing import Dict


@dataclass
class MarginBreakdown:
    """Dataclass storing Zerodha-style margin calculator requirements."""

    span_margin: float
    exposure_margin: float
    premium_margin: float
    total_blocked_margin: float
    available_cash: float
    portfolio_margin: float
    margin_utilized_pct: float


class RealMarginEngine:
    """Real Margin Engine computing Zerodha-style SPAN & Exposure Margins."""

    @classmethod
    def calculate_margin(
        cls,
        quantity: int,
        price: float,
        is_selling: bool = False,
        total_capital: float = 1000000.0,
    ) -> MarginBreakdown:
        """Calculate SPAN + Exposure margin requirements."""
        turnover = price * quantity

        if is_selling:
            span_m = round(turnover * 0.15, 2)
            exp_m = round(turnover * 0.05, 2)
            prem_m = 0.0
        else:
            span_m = 0.0
            exp_m = 0.0
            prem_m = round(turnover, 2)

        blocked = round(span_m + exp_m + prem_m, 2)
        avail = round(total_capital - blocked, 2)
        util_pct = round((blocked / total_capital) * 100.0, 2)

        return MarginBreakdown(
            span_margin=span_m,
            exposure_margin=exp_m,
            premium_margin=prem_m,
            total_blocked_margin=blocked,
            available_cash=avail,
            portfolio_margin=blocked,
            margin_utilized_pct=util_pct,
        )
