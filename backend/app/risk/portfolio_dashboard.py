"""Sensibull-Style Portfolio Dashboard & Rejected Signals Engine."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SensibullPortfolioHeader:
    """Dataclass storing Sensibull-style header summary metrics."""

    total_pnl: float
    unbooked_pnl: float
    booked_pnl: float
    total_decay: float
    total_capital: float
    available_cash: float
    margin_used: float
    exposure_pct: float
    portfolio_delta: float
    portfolio_gamma: float
    portfolio_theta: float
    portfolio_vega: float


class SensibullPortfolioDashboard:
    """Sensibull-Style Portfolio Dashboard Generator."""

    @classmethod
    def get_sensibull_header(cls) -> SensibullPortfolioHeader:
        """Return Sensibull-style portfolio summary header."""
        return SensibullPortfolioHeader(
            total_pnl=-26810.0,
            unbooked_pnl=-33332.0,
            booked_pnl=6522.0,
            total_decay=0.0,
            total_capital=1000000.0,
            available_cash=785000.0,
            margin_used=215000.0,
            exposure_pct=21.5,
            portfolio_delta=45.2,
            portfolio_gamma=0.85,
            portfolio_theta=-1250.0,
            portfolio_vega=620.0,
        )
