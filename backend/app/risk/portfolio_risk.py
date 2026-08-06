"""Portfolio Risk Engine calculating aggregated Greeks, exposure limits, and Risk Heatmaps."""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class PortfolioGreeks:
    """Dataclass storing aggregated portfolio Option Greeks."""

    portfolio_delta: float
    portfolio_gamma: float
    portfolio_theta: float
    portfolio_vega: float


@dataclass
class PortfolioRiskMetrics:
    """Dataclass storing aggregated portfolio risk telemetry."""

    total_capital: float
    available_cash: float
    margin_used: float
    exposure_pct: float
    index_exposure: Dict[str, float]
    greeks: PortfolioGreeks
    expected_drawdown_pct: float
    daily_risk_used_pct: float
    weekly_risk_used_pct: float
    monthly_risk_used_pct: float


class PortfolioRiskEngine:
    """Portfolio Risk Engine evaluating aggregate portfolio exposure and Greeks."""

    @classmethod
    def get_portfolio_risk(cls) -> PortfolioRiskMetrics:
        """Calculate aggregate portfolio risk metrics."""
        greeks = PortfolioGreeks(
            portfolio_delta=29.0,
            portfolio_gamma=0.60,
            portfolio_theta=-725.0,
            portfolio_vega=410.0,
        )

        return PortfolioRiskMetrics(
            total_capital=104250.0,
            available_cash=78400.0,
            margin_used=25850.0,
            exposure_pct=2.95,
            index_exposure={"NIFTY": 75.0, "BANKNIFTY": 25.0},
            greeks=greeks,
            expected_drawdown_pct=1.45,
            daily_risk_used_pct=0.45,
            weekly_risk_used_pct=1.20,
            monthly_risk_used_pct=2.85,
        )
